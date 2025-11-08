use std::io::{self, Write};
use scanpw::scanpw;
use reqwest::Client;
use serde::Serialize;
use std::error::Error;
use std::fs;
use serde_json::Value;

pub async fn fetch_post<B: Serialize>(
    server_host: &str,
    endpoint: &str,
    port: u16,
    body: &B,
) -> Result<String, Box<dyn Error>> {
    // Build URL, allowing the endpoint to be provided with or without leading slash
    let endpoint: String = if endpoint.starts_with('/') {
        endpoint.to_string()
    } else {
        format!("/{}", endpoint)
    };
    let url: String = format!("{}:{}{}", server_host, port, endpoint);

    let client: Client = Client::new();

    let response_text = client
        .post(&url)
        .json(body)        // sets Content-Type: application/json and serializes the body
        .send()
        .await? // convert HTTP errors to Err so callers see non-2xx as Err
        .text()
        .await?;

    Ok(response_text)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("Hello, world!");
    let mut session_id: String = String::new();
    let mut server_host = "https://localhost".to_owned();
    let mut port: u16 = 5912;
    loop {
        print!("> ");
        io::stdout().flush().expect("Something went wrong");
        let mut command: String = String::new();
        io::stdin()
            .read_line(&mut command)
            .expect("Something went wrong");
        match command.trim() {
            "login" => {
                print!("Enter a username: ");
                io::stdout().flush().expect("Something went wrong");
                let mut username: String = String::new();
                io::stdin()
                    .read_line(&mut username)
                    .expect("Something went wrong");
                let password: String = scanpw!("Enter a password: ");
                
                #[derive(Serialize)]
                struct LoginPayload {
                    username: String,
                    password: String
                }
                let payload: LoginPayload = LoginPayload {
                    username: username,
                    password: password,
                };
                
                let resp: String = fetch_post(&server_host, "/login", port, &payload).await.expect("Something went wrong");
                let parsed: Value = serde_json::from_str(&resp).expect("Something went wrong while parsing data");
                
                if parsed["success"].as_bool().unwrap_or(false) {
                    session_id = parsed["newSessionId"].as_str().unwrap_or("").to_owned();
                    println!("Successfully logged in")
                } else {
                    println!("{}",resp);
                }
            }
            
            "register" => {
                print!("Enter a username: ");
                io::stdout().flush().expect("Something went wrong");
                let mut username: String = String::new();
                io::stdin()
                    .read_line(&mut username)
                    .expect("Something went wrong");
                
                let password: String = scanpw!("Enter a password: ");
                print!("Enter the path to your public key file (required): ");
                io::stdout().flush().expect("Something went wrong");
                let mut pubkeypath: String = String::new();
                io::stdin()
                    .read_line(&mut pubkeypath)
                    .expect("Something went wrong");
                pubkeypath = pubkeypath.trim().to_owned();
                let pubkey: String = fs::read_to_string(pubkeypath).expect("Error Reading File");
                
                #[derive(Serialize)]
                struct RegistrationPayload {
                    username: String,
                    password: String,
                    pubkey: String
                }
                
                let registration_payload: RegistrationPayload = RegistrationPayload {
                    username: username,
                    password: password,
                    pubkey: pubkey
                };
                
                let resp: String = fetch_post(&server_host, "/createAccount", port, &registration_payload).await.expect("Something went wrong");
                let parsed: Value = serde_json::from_str(&resp).expect("Something went wrong while parsing data");
                
                if parsed["success"].as_bool().unwrap_or(false) {
                    session_id = parsed["newSessionId"].as_str().unwrap_or("").to_owned();
                } else {
                    println!("{}", resp)
                }
            }
            
            "push" => {
                // Get programid
                print!("Enter an id for the program: ");
                io::stdout().flush().expect("Something went wrong");
                let mut programid: String = String::new();
                io::stdin().read_line(&mut programid).expect("Something went wrong");
                
                // Get programname
                print!("Enter a program name (can leave blank if the program is being amended): ");
                io::stdout().flush().expect("Something went wrong");
                let mut programname: String = String::new();
                io::stdin().read_line(&mut programname).expect("Something went wrong");
                
                // Get path to packaged program
                print!("Enter the path to the packaged program: ");
                io::stdout().flush().expect("Something went wrong");
                let mut packaged_program_path: String = String::new();
                io::stdin().read_line(&mut packaged_program_path).expect("Something went wrong");
                packaged_program_path = packaged_program_path.trim().to_owned();
                
                // Get packaged program from path
                let program_data: String = fs::read_to_string(packaged_program_path).expect("Something went wrong");
                
                #[derive(Serialize)]
                struct PushPayload {
                    programid: String,
                    programname: String,
                    session_id: String,
                    program_data: String
                }
                
                let push_payload: PushPayload = PushPayload {
                    programid: programid,
                    programname: programname,
                    session_id: session_id.clone(),
                    program_data: program_data
                };
                
                // Make a POST request to the server
                let resp: String = fetch_post(&server_host, "/pushProgram", port, &push_payload).await.expect("Something went wrong");
                //let parsed: Value = serde_json::from_str(&resp).expect("Something went wrong while parsing data");
                
                println!("{}", resp);
            }
            
            "host" => {
                print!("Enter the hostname of the server without the port: ");
                io::stdout().flush().expect("Something went wrong");
                io::stdin().read_line(&mut server_host).expect("Error reading line");
                print!("Enter the port: ");
                io::stdout().flush().expect("Something went wrong");
                let mut str_port: String = String::new();
                io::stdin().read_line(&mut str_port).expect("Error reading line");
                if str_port != "".to_owned() {
                    match str::trim(&str_port).parse::<u16>() {
                        Ok(num) => {
                            port = num;
                        }
                        Err(_e) => {
                            println!("Invalid port {} entered", str_port);
                        }
                    };
                }
            }
            
            "exit" => {
                break;
            }
            
            other => {
                println!("Unknown command {}", other)
            }
        }
    }
    
    Ok(())
}
