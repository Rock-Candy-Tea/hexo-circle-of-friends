use reqwest_middleware::ClientWithMiddleware;
use serde_json::json;
use tracing::info;

const MODELS: [&str; 3] = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
];

pub async fn generate_content(client: &ClientWithMiddleware, html: &str) {
    // 从asset获取url

    let gemini_api_key = tools::get_env_var("GEMINI_API_KEY").unwrap();
    if let Some(model) = MODELS.into_iter().next() {
        let body = json!({
            "system_instruction": {
                "parts": [
                    {
                        "text": r#"You are a literary expert specializing in text and article analysis. Your task is to analyze the provided HTML page, extract the blog post contained within it, and
  summarize the article.

  You must adhere to the following strict rules for your response:
   1. The summary must be written in Chinese.
   2. The total length of the summary must not exceed 500 characters but close to 500 (this count includes all characters, punctuation, and spaces).
   3. The output must consist only of the summary text itself. Do not include any prefixes, titles, or introductory phrases (e.g., "Here is the summary:")."#
                    }
                ]
            },
            "contents": [
                {
                    "parts": [
                        {
                            "text": html
                        }
                    ]
                }
            ]
        });
        let body_str = json!(body).to_string();
        println!("{body_str}");
        let res = client
            .post(format!(
                "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
            ))
            .body(body_str)
            .header("Content-Type", "application/json");
        let res = res.send().await.unwrap();
        info!("{}-{}", model, res.text().await.unwrap());
    }
}
