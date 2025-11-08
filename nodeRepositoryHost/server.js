require('dotenv').config();
const port = 5912 || process.env.PORT;
const fs = require('fs');
const https = require('https');
const crypto = require('crypto');
const express = require('express');
const app = express();
const ONE_DAY_IN_MS = 1000 * 60 * 60 * 24;

// Load data
let programs = {}
let users = {}
let usernameToUsers = {}
let sessions = {} // This is not saved as it resets every time the server shuts down
if (fs.existsSync('./data/repository.json')) {
    programs = JSON.parse(fs.readFileSync('./data/repository.json').toString());
}
if (fs.existsSync('./data/users.json')) {
    users = JSON.parse(fs.readFileSync('./data/users.json').toString());
}
if (fs.existsSync('./data/usernameToUsers.json')) {
    usernameToUsers = JSON.parse(fs.readFileSync('./data/usernameToUsers.json').toString());
}

// SSL Options
const options = {
    key: fs.readFileSync('./sslcfg/privateKey.pem'),
    cert: fs.readFileSync('./sslcfg/fullChain.pem')
}

// Functions
function sha256sum(data) {
    return crypto.createHash('sha256').update(data).digest('hex');
}

/**
 * Verify RSA-PSS SHA-256 signature matching the Python verifier behaviour.
 *
 * @param {string} publicPem - PEM string including -----BEGIN PUBLIC KEY----- / -----END PUBLIC KEY-----
 * @param {Buffer|Object} signature - Buffer OR an object like { type: "Buffer", data: [ ... ] }
 * @param {string} message - UTF-8 string; function will compute sha256(message).hexdigest() and use that ASCII hex bytes (matches your Python)
 * @returns {boolean} - true if signature valid, false otherwise
 */
function verifyRsaPssPem(publicPem, signature, message) {
    if (typeof publicPem !== 'string') {
        throw new TypeError('publicPem must be a string (PEM with headers).');
    }
    publicPem = crypto.createPublicKey(publicPem);
    if (typeof message !== 'string') {
        throw new TypeError('message must be a string (UTF-8).');
    }

    // Normalize signature: accept Buffer, or { type: 'Buffer', data: [...] } like JSON.stringify(Buffer)
    let sigBuf;
    if (Buffer.isBuffer(signature)) {
        sigBuf = signature;
    } else if (
        signature &&
        typeof signature === 'object' &&
        signature.type === 'Buffer' &&
        Array.isArray(signature.data)
    ) {
        sigBuf = Buffer.from(signature.data);
    } else {
        throw new TypeError('signature must be a Buffer or { type: "Buffer", data: [...] } object.');
    }

    // Compute sha256(message).hexdigest() and use ASCII hex bytes,
    // because the Python code did: hashlib.sha256(pycode.encode()).hexdigest().encode()
    const hexAscii = crypto.createHash('sha256').update(Buffer.from(message).toString('base64'), 'utf8').digest('hex');
    console.log(hexAscii);
    const dataBuf = Buffer.from(hexAscii, 'utf8');

    // Determine salt length constant (Node versions differ)
    const constants = crypto.constants;
    const saltLength =
    // prefer explicit maximum constants if present
    constants.RSA_PSS_SALTLEN_MAX_SIGN ?? constants.RSA_PSS_SALTLEN_MAX ?? constants.RSA_PSS_SALTLEN_AUTO ?? 32;

    try {
        const ok = crypto.verify(
            'sha256',
            dataBuf,
            {
            key: publicPem,
            padding: crypto.constants.RSA_PKCS1_PSS_PADDING,
            saltLength,
            },
            sigBuf
        );
        return !!ok;
    } catch (err) {
        // For an invalid signature verify() returns false; other errors (bad key, etc.) throw.
        // Re-throw fatal errors so caller can see them.
        throw err;
    }
}

app.use(express.json());

// Have a GET request possible on /
app.get('/', (req, res) => {
    res.send(fs.readFileSync('index.html').toString());
});

// Have a GET request possible on /latest
app.get('/latest', (req, res) => {
    let program = req.query.program;
    if (program in programs) {
        let programData = programs[program];
        res.send(programData['latest']);
    }
});

// Have a GET request possible on /createAccount

// Have a POST request possible on /createAccount
app.post('/createAccount', (req, res) => {
    let username = req.body.username.trim();
    let password = req.body.password.trim();
    let pubkey = req.body.pubkey;
    let salt = crypto.randomBytes(32).toString('hex');
    password = sha256sum(password + salt);
    let newUser = {
        'username': username,
        'password': password,
        'salt': salt,
        'pubkey': pubkey,
        'programs': [],
        'canApprovePrograms': false
    };
    let uuid = crypto.randomUUID().toString();
    let i = 0;
    if (username in usernameToUsers) {
        res.statusCode = 400;
        res.send({
            'message': 'Username already exists',
            'statusCode': 400,
            'proposedSolution': [
                'Choose a different username if this is not your account',
                'POST to /login instead if this is your account'
            ],
            'success': false
        });
    }
    while (uuid in Object.keys(users)) {
        if (i >= 500) {
            res.statusCode = 500;
            res.json({
                'message': 'We could not find you a suitable UUID',
                'statusCode': 500,
                'proposedSolution': 'Try again with the same data',
                'success': false
            });
        }
        uuid = crypto.randomUUID();
        i++;
    }
    users[uuid] = newUser;
    fs.writeFileSync('./data/users.json', JSON.stringify(users));
    usernameToUsers[username] = uuid;
    fs.writeFileSync('./data/usernameToUsers.json', JSON.stringify(usernameToUsers));
    
    let sessionId = crypto.randomUUID().toString();
    if (sessionId in sessions) {
        res.statusCode = 500;
        res.send({
            'message': 'We could not find you a suitable sessionId',
            'statusCode': 500,
            'proposedSolution': 'Make a POST request to /login (use the login command if you\'re using official tools)',
            'success': false
        });
        return;
    }
    let sessionExpiry = new Date().getTime() + ONE_DAY_IN_MS;
    sessions[sessionId] = {
        'expiry': sessionExpiry,
        'user': uuid
    }
    res.statusCode = 200;
    res.json({
        'newSessionId': sessionId,
        'success': true,
        'uuid': uuid,
        'sessionExpiry': sessionExpiry
    });
});

// Have a GET request possible on /login

// Have a POST request possible on /login
app.post('/login', (req, res) => {
    let username = req.body.username.trim();
    let password = req.body.password.trim();
    let uuid = usernameToUsers[username];
    if (!uuid) {
        res.statusCode = 401;
        res.json({
            'message': 'Username/password pair does not exist within repository',
            'success': false
        });
        return;
    }
    let user = users[uuid];
    if (!user) {
        res.statusCode = 500;
        res.send({
            'message': 'Username has a uuid, but we could not find your user entry',
            'success': false
        });
        return;
    }
    let salt = user['salt'];
    password = sha256sum(password + salt);
    if (password != user['password']) {
        res.statusCode = 401;
        res.json({
            'message': 'Username/password pair does not exist within repository',
            'success': false
        });
        return;
    }
    
    let sessionId = crypto.randomUUID().toString();
    if (sessionId in sessions) {
        res.statusCode = 500;
        res.json({
            'message': 'We could not find you a suitable sessionId',
            'statusCode': 500,
            'proposedSolution': 'Try again with the same body in the post (if you\'re using official tools, just try again with the same credentials)',
            'success': false
        });
        return;
    }
    let sessionExpiry = new Date().getTime() + ONE_DAY_IN_MS;
    sessions[sessionId] = {
        'expiry': sessionExpiry,
        'user': uuid
    }
    res.statusCode = 200;
    res.json({
        'newSessionId': sessionId,
        'success': true,
        'uuid': uuid,
        'sessionExpiry': sessionExpiry
    });
});

// Have a GET request possible on /newProgram

// Have a POST request possible on /pushProgram
app.post('/pushProgram', (req, res) => {
    let programid = req.body.programid.trim();
    let programname = req.body.programname.trim();
    let sessionId = req.body.session_id.trim();
    let programData = req.body.program_data.trim();
    
    if (!(programData)) {
        res.statusCode = 400;
        res.json({
            'statusCode': 400,
            'message': 'No program data was provided',
            'proposedSolution': 'Provide program data in program_data of the body',
            'success': false
        })
    }
    
    if ((typeof programData) == 'string') {
        programData = JSON.parse(programData);
    }
    
    if (!(sessionId in sessions)) {
        res.statusCode = 401;
        res.json({
            'statusCode': 401,
            'message': 'Invalid sessionId',
            'proposedSolution': 'Log in by posting the credentials to /login (on the ROSCtools, you can use the login option)',
            'success': false
        });
        return;
    }
    let userUUID = sessions[sessionId]['user'];
    
    if (!(/^[_0-9a-zA-Z\-]+$/.test(programid))) {
        res.statusCode = 400;
        res.json({
            'statusCode': 400,
            'message': 'Invalid programid (must follow regex: /^[_0-9a-zA-Z\\-]*$/)',
            'proposedSolution': 'Try again with a different program name',
            'success': false
        });
        return;
    }
    
    programData['origin'] = process.env.ORIGIN + ':' + port;
    programData['repo-signature'] = null;
    programData['recalled-or-rescinded'] = false;
    
    let version = programData['version-int'];
    if ((version === undefined) || (version === null)) {
        res.statusCode = 400;
        res.json({
            'message': 'No version-int specified',
            'proposedSolution': 'Specify an integer version in the program metadata by adding a field "version-int" in the program metadata',
            'success': false
        });
        return;
    }
    if (((typeof version) != 'number') || (version < 0) || (version != Math.floor(version))) {
        res.statusCode = 400;
        res.json({
            'message': 'version-int is not a whole number',
            'proposedSolution': 'Ensure your version-int is a non-negative integer (not a string)',
            'success': false
        });
        return;
    }
    
    programData['uploaded-by'] = userUUID;
    
    if (programid in programs) {
        // Program already exists, amend program
        
        // Check that latest version is not above the version being submitted
        let latest = programs[programid]['latest'];
        if (latest >= version) {
            res.statusCode = 400;
            res.json({
                'message': 'Latest version exceeds or equals version being pushed',
                'proposedSolution': `Increase the version to a version above ${latest}, such as ${latest + 1}`,
                'success': false
            });
            return;
        }
        
        // Check signature
        let signature = programData['signature'];
        if (!signature) {
            res.statusCode = 400;
            res.json({
                'message': 'Code lacks a signature',
                'success': false,
                'proposedSolution': 'Try repackaging it with officially supported methods'
            });
            return;
        }
        signature = Buffer.from(signature, 'base64');
        let code = programData['code'];
        let codeDecoded = Buffer.from(code, 'base64').toString('utf-8');
        let primaryProgrammer = programs[programid]['primary-programmer'];
        if (primaryProgrammer in users) {
            res.statusCode = 500;
            res.json({
                'message': 'Primary programmer is not in our users dictionary',
                'success': false
            });
            return;
        }
        let pubkey = users[primaryProgrammer]['pubkey'].trim();
        if (!pubkey) {
            res.statusCode = 500;
            res.json({
                'message': 'Primary programmer does not have a public key listed',
                'success': false
            });
            return;
        }
        let progpubkey = programData['publickey'];
        if (!progpubkey) {
            progpubkey = programData['publickey'];
            programData['publickey'] = Buffer.from(pubkey, 'utf-8').toString('base64');
        } else {
            progpubkey = Buffer.from(pubkey, 'base64').toString('utf-8');
        }
        if (progpubkey !== pubkey) {
            res.statusCode = 400;
            res.json({
                'message': 'An incorrect progpubkey has been provided',
                'statusCode': 400,
                'proposedSolution': `Ensure the program is signed with ${primaryProgrammer}'s keypair`,
                'success': false
            })
        }
        let validated = verifyRsaPssPem(pubkey, signature, codeDecoded);
        if (!validated) {
            res.statusCode = 400;
            res.json({
                'message': 'Signature validation failed',
                'proposedSolution': [
                    'Use official packaging software to package the program',
                    'Ensure your private key used to sign the program coincides with the public key listed on the program metadata'
                ],
                'success': false
            });
            return;
        }
        
        // Check for user authorisation to push program
        let authorisedUsers = programs[programid]['authorised-users'];
        if (!(userUUID in authorisedUsers)) {
            res.statusCode = 403;
            res.json({
                'message': 'You are not authorised to push changes to this program',
                'proposedSolutions': [
                    'Log in using an authorised account',
                    `Request authorisation from ${user[primaryProgrammer]['username']}`,
                    'Push the program under a different programid'
                ],
                'success': false
            });
            return;
        }
        
        // Push program
        programs[programid]['releases'][version] = programData;
        fs.writeFileSync('./data/repository.json', JSON.stringify(programs));
        
        // Return a successful result
        res.statusCode = 201;
        res.json({
            'statusCode': 201,
            'message': 'Successfuly amended program',
            'success': true
        });
        return;
    }
    
    // Program is not yet in repository, add program
    
    // Verify signature
    let signature = programData['signature'];
    if (!signature) {
        res.statusCode = 400;
        res.json({
            'message': 'Code lacks a signature',
            'success': false,
            'proposedSolution': 'Try repackaging it with officially supported methods'
        });
        return;
    }
    signature = Buffer.from(signature, 'base64');
    let code = programData['code'];
    let codeDecoded = Buffer.from(code, 'base64').toString('utf-8');
    let pubkey = users[userUUID]['pubkey'];
    if (!pubkey) {
        res.statusCode = 500;
        res.json({
            'message': 'Primary programmer does not have a public key listed',
            'success': false
        });
        return;
    }
    let validated = verifyRsaPssPem(pubkey, signature, codeDecoded);
    if (!validated) {
        res.statusCode = 400;
        res.json({
            'message': 'Signature validation failed',
            'proposedSolution': [
                'Use official packaging software to package the program',
                'Ensure your private key used to sign the program coincides with the public key listed on the program metadata'
            ],
            'success': false
        });
        return;
    }
    
    // Prepare to push
    program = {
        'latest': version,
        'authorised-users': [userUUID],
        'primary-programmer': userUUID,
        'releases': {
            version: programData
        },
        'latest-approved': null,
        'program-name': programname,
        'program-descripion': null
    }
    
    // Push the program to the repository
    programs[programid] = program;
    fs.writeFileSync('./data/repository.json', JSON.stringify(programs));
        
    // Return a successful result
    res.statusCode = 201;
    res.json({
        'statusCode': 201,
        'message': 'Successfuly added program',
        'success': true
    });
    return;
});

// Have a GET request possible on /updateProgram

// Have a POST request possible on /updateProgram

// Have a GET request possible on /downloadProgram

// Have a GET request possible on /style.css

const server = https.createServer(options, app);
server.listen(port, () => {
    console.log(`RandOS Repository for NodeJS listening on port ${port}`);
})