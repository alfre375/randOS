const port = 5912 || process.env.port;
const fs = require('fs');
const https = require('https');
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

app.use(express.json());

// Have a GET request possible on /
app.get('/', (req, res) => {
    res.send(fs.readFileSync('index.html'))
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
    let username = req.body.username;
    let password = req.body.password;
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
        res.send('Username already exists')
    }
    while (uuid in Object.keys(users)) {
        if (i >= 500) {
            res.statusCode = 500;
            res.send('Unable to get a valid UUID for user');
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
        res.send('We could not find you a suitable sessionId. Please try again.');
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
    let username = req.body.username;
    let password = req.body.password;
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
        res.send('We could not find you a suitable sessionId. Please try again.');
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

// Have a POST request possible on /newProgram
app.post('/newProgram', (req, res) => {
    let programid = req.body.programid;
    let programname = req.body.programname;
    let sessionId = req.body.sessionId;
    let programData = req.body.programData;
    if (!(sessionId in sessions)) {
        res.statusCode = 401;
        res.json({
            'statusCode': 401,
            'message': 'Invalid sessionId',
            'success': false
        });
        return;
    }
})

// Have a GET request possible on /updateProgram

// Have a POST request possible on /updateProgram

// Have a GET request possible on /downloadProgram

// Have a GET request possible on /style.css

const server = https.createServer(options, app);
server.listen(port, () => {
    console.log(`RandOS Repository for NodeJS listening on port ${port}`);
})