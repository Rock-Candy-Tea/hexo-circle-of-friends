#[cfg(test)]
mod tests {
    use crate::config::*;

    #[test]
    fn test_generate_summary_config_deserialization() {
        let yaml_content = r#"
enabled: true
provider: "gemini"
max_concurrent: 5
wait_on_rate_limit: false
max_chars: 10000
gemini:
  models: ["gemini-2.5-flash", "gemini-2.5-pro"]
siliconflow:
  models: ["THUDM/GLM-4.1V-9B-Thinking", "Qwen/Qwen3-8B", "THUDM/glm-4-9b-chat"]
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.provider, "gemini");

        // 验证简化配置
        assert_eq!(config.get_max_concurrent(), 5);
        assert!(!config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 10000);
        assert_eq!(config.get_chunk_size(), 5000); // 自动计算为一半

        assert!(config.gemini.is_some());
        let gemini_config = config.gemini.unwrap();
        assert_eq!(gemini_config.models.len(), 2);
        assert!(
            gemini_config
                .models
                .contains(&"gemini-2.5-flash".to_string())
        );
        assert!(gemini_config.models.contains(&"gemini-2.5-pro".to_string()));

        assert!(config.siliconflow.is_some());
        let siliconflow_config = config.siliconflow.unwrap();
        assert_eq!(siliconflow_config.models.len(), 3);
        assert!(
            siliconflow_config
                .models
                .contains(&"THUDM/GLM-4.1V-9B-Thinking".to_string())
        );
        assert!(
            siliconflow_config
                .models
                .contains(&"Qwen/Qwen3-8B".to_string())
        );
        assert!(
            siliconflow_config
                .models
                .contains(&"THUDM/glm-4-9b-chat".to_string())
        );
    }

    #[test]
    fn test_generate_summary_config_disabled() {
        let yaml_content = r#"
enabled: false
provider: "gemini"
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(!config.enabled);
        assert_eq!(config.provider, "gemini");
    }

    #[test]
    fn test_generate_summary_config_siliconflow_only() {
        let yaml_content = r#"
enabled: true
provider: "siliconflow"
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
siliconflow:
  models: ["THUDM/GLM-4.1V-9B-Thinking", "Qwen/Qwen3-8B", "THUDM/glm-4-9b-chat"]
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.provider, "siliconflow");
        assert!(config.gemini.is_none());

        assert!(config.siliconflow.is_some());
        let siliconflow_config = config.siliconflow.unwrap();
        assert_eq!(siliconflow_config.models.len(), 3);
        assert!(
            siliconflow_config
                .models
                .contains(&"THUDM/GLM-4.1V-9B-Thinking".to_string())
        );
        assert!(
            siliconflow_config
                .models
                .contains(&"Qwen/Qwen3-8B".to_string())
        );
        assert!(
            siliconflow_config
                .models
                .contains(&"THUDM/glm-4-9b-chat".to_string())
        );
    }

    #[test]
    fn test_generate_summary_config_serialization() {
        let config = GenerateSummaryConfig {
            enabled: true,
            provider: "gemini".to_string(),
            max_concurrent: 3,
            wait_on_rate_limit: true,
            max_chars: 8000,
            gemini: Some(ModelConfig {
                models: vec!["gemini-2.5-flash".to_string()],
            }),
            siliconflow: Some(ModelConfig {
                models: vec!["Qwen/QwQ-32B".to_string()],
            }),
            bigmodel: Some(ModelConfig {
                models: vec!["glm-4-flashx-250414".to_string()],
            }),
        };

        let yaml_str = serde_yaml::to_string(&config).unwrap();

        // 验证可以重新解析
        let parsed_config: GenerateSummaryConfig = serde_yaml::from_str(&yaml_str).unwrap();
        assert_eq!(parsed_config.enabled, config.enabled);
        assert_eq!(parsed_config.provider, config.provider);
    }

    #[test]
    fn test_gemini_config_empty_models() {
        let yaml_content = r#"
enabled: true
provider: "gemini"
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
gemini:
  models: []
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.provider, "gemini");

        assert!(config.gemini.is_some());
        let gemini_config = config.gemini.unwrap();
        assert!(gemini_config.models.is_empty());
    }

    #[test]
    fn test_siliconflow_config_empty_models() {
        let yaml_content = r#"
enabled: true
provider: "siliconflow"
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
siliconflow:
  models: []
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.provider, "siliconflow");

        assert!(config.siliconflow.is_some());
        let siliconflow_config = config.siliconflow.unwrap();
        assert!(siliconflow_config.models.is_empty());
    }

    #[test]
    fn test_generate_summary_config_clone() {
        let original = GenerateSummaryConfig {
            enabled: true,
            provider: "gemini".to_string(),
            max_concurrent: 3,
            wait_on_rate_limit: true,
            max_chars: 8000,
            gemini: Some(ModelConfig {
                models: vec!["gemini-2.5-flash".to_string()],
            }),
            siliconflow: None,
            bigmodel: None,
        };

        let cloned = original.clone();

        assert_eq!(original.enabled, cloned.enabled);
        assert_eq!(original.provider, cloned.provider);
        assert_eq!(
            original.gemini.as_ref().unwrap().models,
            cloned.gemini.as_ref().unwrap().models
        );
    }

    #[test]
    fn test_generate_summary_config_all_provider() {
        let yaml_content = r#"
enabled: true
provider: "all"
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
gemini:
  models: ["gemini-2.5-flash"]
siliconflow:
  models: ["THUDM/GLM-4.1V-9B-Thinking", "Qwen/Qwen3-8B"]
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.provider, "all");

        assert!(config.gemini.is_some());
        let gemini_config = config.gemini.unwrap();
        assert_eq!(gemini_config.models.len(), 1);
        assert!(
            gemini_config
                .models
                .contains(&"gemini-2.5-flash".to_string())
        );

        assert!(config.siliconflow.is_some());
        let siliconflow_config = config.siliconflow.unwrap();
        assert_eq!(siliconflow_config.models.len(), 2);
        assert!(
            siliconflow_config
                .models
                .contains(&"THUDM/GLM-4.1V-9B-Thinking".to_string())
        );
        assert!(
            siliconflow_config
                .models
                .contains(&"Qwen/Qwen3-8B".to_string())
        );
    }

    #[test]
    fn test_generate_summary_config_dict_format() {
        // 测试大括号dict格式
        let yaml_content = r#"
enabled: true
provider: "siliconflow"
max_concurrent: 3
wait_on_rate_limit: true
max_chars: 8000
siliconflow: {
  models: ["THUDM/GLM-4.1V-9B-Thinking", "Qwen/Qwen3-8B"]
}
"#;

        let config: GenerateSummaryConfig = serde_yaml::from_str(yaml_content).unwrap();

        assert!(config.enabled);
        assert_eq!(config.provider, "siliconflow");
        assert!(config.gemini.is_none());

        assert!(config.siliconflow.is_some());
        let siliconflow_config = config.siliconflow.unwrap();
        assert_eq!(siliconflow_config.models.len(), 2);
        assert!(
            siliconflow_config
                .models
                .contains(&"THUDM/GLM-4.1V-9B-Thinking".to_string())
        );
        assert!(
            siliconflow_config
                .models
                .contains(&"Qwen/Qwen3-8B".to_string())
        );
    }

    #[test]
    fn test_default_values() {
        let config = GenerateSummaryConfig {
            enabled: true,
            provider: "all".to_string(),
            max_concurrent: 3,
            wait_on_rate_limit: true,
            max_chars: 8000,
            gemini: None,
            siliconflow: None,
            bigmodel: None,
        };

        // 验证默认值
        assert_eq!(config.get_max_concurrent(), 3);
        assert!(config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 8000);
        assert_eq!(config.get_chunk_size(), 4000);
        assert_eq!(config.get_retry_attempts(), 3);
        assert_eq!(config.get_rate_limit_delay(), 60);
    }

    #[test]
    fn test_custom_values() {
        let config = GenerateSummaryConfig {
            enabled: true,
            provider: "all".to_string(),
            max_concurrent: 5,
            wait_on_rate_limit: false,
            max_chars: 12000,
            gemini: None,
            siliconflow: None,
            bigmodel: None,
        };

        // 验证自定义值
        assert_eq!(config.get_max_concurrent(), 5);
        assert!(!config.get_wait_on_rate_limit());
        assert_eq!(config.get_max_chars(), 12000);
        assert_eq!(config.get_chunk_size(), 6000); // 自动计算为一半
    }
}
