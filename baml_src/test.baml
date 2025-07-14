class WeatherAPI {
  city string @description("the user's city")
  timeOfDay string @description("As an ISO8601 timestamp")
}

function UseTool(user_message: string) -> WeatherAPI {
  client "openai/gpt-4o"
  prompt #"
    Extract.... {# we will explain the rest in the guides #}
  "#
}
