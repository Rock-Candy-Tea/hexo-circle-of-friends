use db::mongo;
use tracing::{error, info};

#[tokio::main]
async fn main() {
    let _guard = tools::init_tracing("tmptest", Some("trace"));
    let mongodburi = match tools::get_env_var("MONGODB_URI") {
        Ok(mongodburi) => {
            info!("MONGODB_URI: {}", mongodburi);
            mongodburi
        }
        Err(e) => {
            error!("{}", e);
            return;
        }
    };
    let _clientdb = match mongo::connect_mongodb_clientdb(&mongodburi).await {
        Ok(clientdb) => clientdb,
        Err(e) => {
            error!("{}", e);
            return;
        }
    };
}
