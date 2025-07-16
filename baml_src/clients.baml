// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview
client<llm> VLLM {
  provider "openai-generic"
  options {
    base_url env.MODEL_HOST
    api_key env.MODEL_API_KEY
    model env.MODEL_NAME
    default_role "user" // Required for using VLLM
    temperature 0.7
    top_p 0.8
    top_k 20
    repetition_penalty 1.05

  }
}

client<llm> VLLM2 {
  provider "openai-generic"
  options {
    base_url env.MODEL_HOST
    api_key env.MODEL_API_KEY
    model env.MODEL_NAME
    default_role "user" // Required for using VLLM
    temperature 0
    top_p 0.8
    top_k 20
    repetition_penalty 1.05
    seed 123
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  // Strategy is optional
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  // Strategy is optional
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}