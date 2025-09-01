use reqwest_middleware::ClientWithMiddleware;
use serde_json::json;
use tracing::info;

const MODELS: [&str; 3] = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
];

pub async fn generate_content(
    client: &ClientWithMiddleware,
    html: &str,
) -> Result<String, Box<dyn std::error::Error>> {
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
   1. The summary must be written in Simplified Chinese, if not, translate it to Simplified Chinese.
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
        let res = client
            .post(format!(
                "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
            ))
            .body(body_str)
            .header("Content-Type", "application/json")
            .send()
            .await?;

        let response_text = res.text().await?;
        info!("{} API response: {}", model, response_text);

        // Parse the response to extract the summary
        let response_json: serde_json::Value = serde_json::from_str(&response_text)?;

        if let Some(candidates) = response_json["candidates"].as_array()
            && let Some(first_candidate) = candidates.first()
            && let Some(content) = first_candidate["content"]["parts"].as_array()
            && let Some(first_part) = content.first()
            && let Some(text) = first_part["text"].as_str()
        {
            return Ok(text.to_string());
        }

        Err("Failed to extract summary from Gemini response".into())
    } else {
        Err("No available Gemini model".into())
    }
}
