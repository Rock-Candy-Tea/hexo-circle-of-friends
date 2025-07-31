use regex::Regex;

/// HTML内容提取和精简工具
pub struct HtmlExtractor {
    /// 最大字符数限制
    max_chars: usize,
    /// 分块大小
    chunk_size: usize,
}

impl HtmlExtractor {
    pub fn new(max_chars: usize, chunk_size: usize) -> Self {
        Self {
            max_chars,
            chunk_size,
        }
    }

    pub fn get_chunk_size(&self) -> usize {
        self.chunk_size
    }

    pub fn get_max_chars(&self) -> usize {
        self.max_chars
    }

    /// 提取HTML中的主要文章内容
    pub fn extract_article_content(&self, html: &str) -> String {
        // 1. 移除脚本和样式标签
        let content = self.remove_scripts_and_styles(html);

        // 2. 提取主要内容区域
        let content = self.extract_main_content(&content);

        // 3. 移除HTML标签，保留纯文本
        let content = self.strip_html_tags(&content);

        // 4. 清理多余的空白字符
        let content = self.clean_whitespace(&content);

        // 5. 限制长度
        if content.len() > self.max_chars {
            content.chars().take(self.max_chars).collect()
        } else {
            content
        }
    }

    /// 将长内容分割成多个块
    pub fn chunk_content(&self, content: &str) -> Vec<String> {
        if content.chars().count() <= self.chunk_size {
            return vec![content.to_string()];
        }

        let mut chunks = Vec::new();
        let chars: Vec<char> = content.chars().collect();
        let mut start = 0;

        while start < chars.len() {
            let end = std::cmp::min(start + self.chunk_size, chars.len());

            // 尝试在句号或换行符处分割，避免截断句子
            let mut chunk_end = end;
            if end < chars.len() {
                // 从end往前找句号
                for i in (start..end).rev() {
                    if chars[i] == '。' || chars[i] == '\n' {
                        chunk_end = i + 1;
                        break;
                    }
                }
            }

            let chunk: String = chars[start..chunk_end].iter().collect();
            chunks.push(chunk);
            start = chunk_end;
        }

        chunks
    }

    /// 移除脚本和样式标签
    fn remove_scripts_and_styles(&self, html: &str) -> String {
        let script_regex = Regex::new(r"(?is)<script[^>]*>.*?</script>").unwrap();
        let style_regex = Regex::new(r"(?is)<style[^>]*>.*?</style>").unwrap();
        let noscript_regex = Regex::new(r"(?is)<noscript[^>]*>.*?</noscript>").unwrap();

        let content = script_regex.replace_all(html, "");
        let content = style_regex.replace_all(&content, "");
        noscript_regex.replace_all(&content, "").to_string()
    }

    /// 提取主要内容区域
    fn extract_main_content(&self, html: &str) -> String {
        // 按优先级尝试提取内容区域
        let content_selectors = [
            // 文章内容相关的标签和类名
            r"<article[^>]*>(.*?)</article>",
            r#"<div[^>]*class="[^"]*(?:post-content|article-content|entry-content|content|main-content)[^"]*"[^>]*>(.*?)</div>"#,
            r#"<div[^>]*id="[^"]*(?:content|main|article|post)[^"]*"[^>]*>(.*?)</div>"#,
            r"<main[^>]*>(.*?)</main>",
            // 如果没有找到特定区域，尝试提取body内容
            r"<body[^>]*>(.*?)</body>",
        ];

        for selector in &content_selectors {
            if let Ok(regex) = Regex::new(&format!("(?is){selector}"))
                && let Some(captures) = regex.captures(html)
                && let Some(matched) = captures.get(1)
            {
                let content = matched.as_str();
                // 如果内容长度合理，就使用这个
                if content.trim().len() > 100 {
                    return content.to_string();
                }
            }
        }

        // 如果都没找到，返回原始HTML
        html.to_string()
    }

    /// 移除HTML标签
    fn strip_html_tags(&self, html: &str) -> String {
        let tag_regex = Regex::new(r"<[^>]*>").unwrap();
        let result = tag_regex.replace_all(html, " ");

        // 解码HTML实体
        self.decode_html_entities(&result)
    }

    /// 解码常见的HTML实体
    fn decode_html_entities(&self, text: &str) -> String {
        text.replace("&nbsp;", " ")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
            .replace("&quot;", "\"")
            .replace("&#39;", "'")
            .replace("&hellip;", "...")
            .replace("&mdash;", "—")
            .replace("&ndash;", "–")
    }

    /// 清理多余的空白字符
    fn clean_whitespace(&self, text: &str) -> String {
        let whitespace_regex = Regex::new(r"\s+").unwrap();
        whitespace_regex.replace_all(text.trim(), " ").to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_article_content() {
        let extractor = HtmlExtractor::new(1000, 500);

        let html = r#"
        <html>
            <head><title>Test</title></head>
            <body>
                <script>console.log('test');</script>
                <article>
                    <h1>测试文章标题</h1>
                    <p>这是文章的第一段内容。</p>
                    <p>这是文章的第二段内容，包含更多详细信息。</p>
                </article>
                <footer>页脚内容</footer>
            </body>
        </html>
        "#;

        let result = extractor.extract_article_content(html);

        assert!(!result.contains("<script>"));
        assert!(!result.contains("<article>"));
        assert!(result.contains("测试文章标题"));
        assert!(result.contains("第一段内容"));
        assert!(result.contains("第二段内容"));
    }

    #[test]
    fn test_chunk_content() {
        let extractor = HtmlExtractor::new(1000, 10); // 10个字符一块

        let content = "这是第一句话。这是第二句话。这是第三句话。这是第四句话。";
        let chunks = extractor.chunk_content(content);

        // 应该在句号处分割
        assert!(chunks.len() > 1);
        if chunks.len() > 1 {
            assert!(chunks[0].ends_with('。'));
        }
    }

    #[test]
    fn test_remove_scripts_and_styles() {
        let extractor = HtmlExtractor::new(1000, 500);

        let html = r#"
        <div>
            <script>alert('test');</script>
            <style>.test { color: red; }</style>
            <p>保留的内容</p>
            <noscript>无脚本内容</noscript>
        </div>
        "#;

        let result = extractor.remove_scripts_and_styles(html);

        assert!(!result.contains("<script>"));
        assert!(!result.contains("<style>"));
        assert!(!result.contains("<noscript>"));
        assert!(result.contains("保留的内容"));
    }

    #[test]
    fn test_strip_html_tags() {
        let extractor = HtmlExtractor::new(1000, 500);

        let html = r#"<div class="test">这是<strong>加粗</strong>的文本，包含&nbsp;特殊字符&amp;实体。</div>"#;
        let result = extractor.strip_html_tags(html);

        assert!(!result.contains("<div>"));
        assert!(!result.contains("<strong>"));
        assert!(result.contains("这是"));
        assert!(result.contains("加粗"));
        assert!(result.contains("的文本"));
        assert!(result.contains("特殊字符"));
    }

    #[test]
    fn test_clean_whitespace() {
        let extractor = HtmlExtractor::new(1000, 500);

        let text = "   这是   多个    空格\n\n\n和换行   的文本   ";
        let result = extractor.clean_whitespace(text);

        assert_eq!(result, "这是 多个 空格 和换行 的文本");
    }
}
