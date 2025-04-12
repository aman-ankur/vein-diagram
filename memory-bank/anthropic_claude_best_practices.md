# Anthropic Claude API: Best Practices Guide

This guide provides project-agnostic recommendations for integrating with the Anthropic Claude API, focusing on reliability, maintainability, and efficiency.

## 1. Authentication & Security

*   **API Keys:** Store your Anthropic API key securely. Use environment variables (e.g., `ANTHROPIC_API_KEY`) rather than hardcoding keys in source code.
*   **Access Control:** Implement appropriate access controls on the server-side where the API key is used. Avoid exposing the key directly to client-side applications.

## 2. SDK Usage

*   **Use the Official SDK:** Prefer using the official Anthropic Python SDK (`pip install anthropic`) over making direct HTTP requests.
    *   **Benefits:** Simplifies API interactions, handles request formatting, provides built-in error types, manages API versioning automatically, and often includes helper functions.
    *   **Example:**
        ```python
        import anthropic
        import os

        client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            timeout=60.0, # Configure timeout directly
        )

        message = client.messages.create(...)
        ```
*   **Consistency:** Use the SDK consistently across all services interacting with Claude.

## 3. API Versioning

*   The official SDK handles the `anthropic-version` header automatically, ensuring you use compatible API versions. If making direct HTTP calls, ensure you use a recent, supported version specified in the Anthropic documentation.

## 4. Model Selection

*   Choose models based on the task requirements:
    *   `claude-3-haiku`: Fastest, most cost-effective for simple tasks, summarization, explanations.
    *   `claude-3-sonnet`: Balanced speed and intelligence for tasks like data extraction, code generation, most enterprise workloads.
    *   `claude-3-opus`: Most powerful model for complex analysis, research, tasks requiring deep reasoning.
*   Test different models to find the best trade-off between performance, cost, and accuracy for your specific use case.

## 5. Prompt Engineering

*   **System Prompts:** Use system prompts effectively to set the context, define the AI's role, specify constraints, and guide its behavior.
    ```python
    message = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        system="You are a helpful assistant expert in extracting structured data from text.", # System prompt
        messages=[
            {"role": "user", "content": "Extract the key entities from the following text: ..."}
        ]
    )
    ```
*   **Clear Instructions:** Be explicit and unambiguous in your user prompts. Clearly state the desired output format, task, and any constraints.
*   **Few-Shot Prompting:** For complex tasks or specific formatting, provide examples within the prompt (`few-shot`) to guide the model.
*   **Iterate:** Prompt engineering is iterative. Test and refine your prompts based on the results.

## 6. Handling Structured Output (e.g., JSON)

*   **Explicit Prompting:** Clearly instruct Claude to return the response *only* in valid JSON format. Specify the exact schema expected. Claude 3 models are significantly better at adhering to these instructions.
    ```python
    prompt = f"""
    Extract the user's name and email from the text below.
    Return the result ONLY as a valid JSON object matching this exact structure:
    {{
      "user": {{
        "name": "...",
        "email": "..."
      }}
    }}
    If a field is not found, use null. Do not include any explanations or surrounding text.

    Text:
    {text_content}
    """
    ```
*   **Parsing & Validation:** Always validate the response to ensure it's valid JSON and conforms to the expected schema before using it.
*   **Minimize Repair:** While some JSON repair logic might be necessary as a fallback, rely primarily on strong prompting to get correct JSON. Excessive repair suggests prompts need improvement.

## 7. Error Handling & Retries

*   **Use SDK Exceptions:** Catch specific exceptions provided by the SDK (`anthropic.APIError`, `anthropic.APIConnectionError`, `anthropic.RateLimitError`, `anthropic.APIStatusError`, etc.) for granular error handling.
*   **Timeouts:** Configure timeouts directly in the SDK client instantiation (`timeout=...`) instead of using custom wrappers where possible.
*   **Retries:** Implement a retry mechanism (e.g., using libraries like `tenacity`) with exponential backoff for transient errors like rate limits (`429`) or server issues (`5xx`).
*   **Fallbacks:** For critical tasks, consider fallback mechanisms (like simpler models, regex, or default values) if the primary API call fails after retries.

## 8. Streaming Responses

*   For user-facing applications where responsiveness is key (e.g., chatbots, explanations), use the streaming API (`client.messages.stream(...)`). This allows you to process and display the response chunk by chunk as it's generated.

## 9. Cost Management

*   **Monitor Usage:** Keep track of your API usage and costs via the Anthropic console.
*   **Choose Appropriate Models:** Use less expensive models (like Haiku) where sufficient.
*   **Optimize Prompts:** Shorter, more efficient prompts consume fewer tokens.
*   **Max Tokens:** Set reasonable `max_tokens` limits to prevent unexpectedly long (and expensive) responses.
*   **Caching:** Implement caching (e.g., using Redis, Memcached, or even in-memory for short-lived data) for frequently requested, identical prompts (like general biomarker explanations).

## 10. Rate Limiting

*   Be aware of Anthropic's rate limits. Implement rate limit handling (retries with backoff) as mentioned in Error Handling. If consistently hitting limits, consider requesting a limit increase or optimizing your application's call patterns. 