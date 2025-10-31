const port = 5912
const fs = require('fs')
const https = require('https')
const express = require('express')
const app = express()

// SSL Options
const options = {
    key: fs.readFileSync('./sslcfg/privateKey.pem'),
    cert: fs.readFileSync('./sslcfg/fullChain.pem')
}

// Have a GET request possible on /
app.get('/', (req, res) => {
    res.send(fs.readFileSync('index.html'))
})

// Have a GET request possible on /latest

// Have a GET request possible on /createAccount

// Have a POST request possible on /createAccount

// Have a GET request possible on /login

// Have a POST request possible on /login

// Have a GET request possible on /newProgram

// Have a POST request possible on /newProgram

// Have a GET request possible on /updateProgram

// Have a POST request possible on /updateProgram

// Have a GET request possible on /downloadProgram

// Have a GET request possible on /style.css