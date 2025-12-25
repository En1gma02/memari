# Batch API

> Run large-scale inference workloads asynchronously at half the cost.

<Callout icon="lock" color="#b2b1b1ff" iconType="regular">
  This feature is in <Badge color="white-destructive">Private Preview.</Badge> For access or more information, [contact us](https://www.cerebras.ai/contact) or reach out to your account representative.
</Callout>

The Batch API lets you process groups of requests asynchronously, making it perfect for workloads where you don't need immediate results:

* **Evaluation pipelines**: Test model performance across thousands of test cases
* **Data labeling**: Classify or annotate large datasets for training
* **Content generation**: Create product descriptions, summaries, or translations in bulk
* **Research and analysis**: Process scientific data or run experiments at scale

You'll get 50% off regular pricing and guaranteed completion within 24 hours.

## How It Works

The basic workflow has four steps:

1. **Prepare a JSONL file** containing all your requests
2. **Upload the file** using the [Files API](/api-reference/file/upload-file)
3. **Submit a batch job** referencing your uploaded file
4. **Download results** once processing completes

Behind the scenes, Cerebras processes your requests during periods of lower demand, which enables the significant cost savings.

## Create a Batch Request

<Steps>
  <Step title="Prepare your input file">
    Start by creating a `.jsonl` file where each line represents one API request. Every request needs a unique `custom_id` so you can match inputs to outputs later. The available endpoint is currently `/v1/chat/completions`.

    Here's what two requests look like:

    ```jsonl  theme={null}
    {"custom_id": "eval-001", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.3-70b", "messages": [{"role": "user", "content": "Summarize the water cycle"}], "max_completion_tokens": 500}}
    {"custom_id": "eval-002", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "llama-3.3-70b", "messages": [{"role": "user", "content": "Explain photosynthesis"}], "max_completion_tokens": 500}}
    ```

    Each line contains the same parameters you'd use in a regular chat completion request, just wrapped in the batch format.

    **Important constraints:**

    * Maximum 200 MB file size
    * Minimum 10 requests
    * Up to 50,000 requests per file
    * Each line limited to 1 MB
    * UTF-8 encoding with LF line endings
    * All requests must use the same model
  </Step>

  <Step title="Upload your file">
    Use the [Files API](/api-reference/file/upload-file) to upload your prepared input file:

    <CodeGroup>
      ```python Python theme={null}
      from cerebras.cloud.sdk import Cerebras

      client = Cerebras(api_key="your-api-key")

      input_file = client.files.create(
          file=open("my_batch_requests.jsonl", "rb"),
          purpose="batch"
      )

      print(f"Uploaded file: {input_file.id}")
      ```

      ```javascript Node.js theme={null}
      import Cerebras from '@cerebras/cerebras_cloud_sdk';
      import fs from 'fs';

      const client = new Cerebras({ apiKey: process.env.CEREBRAS_API_KEY });

      const file = await client.files.create({
        file: fs.createReadStream("my_batch_requests.jsonl"),
        purpose: "batch"
      });

      console.log(`Uploaded file: ${file.id}`);
      ```

      ```bash cURL theme={null}
      curl https://api.cerebras.ai/v1/files \
        -H "Authorization: Bearer $CEREBRAS_API_KEY" \
        -F purpose="batch" \
        -F file="@my_batch_requests.jsonl"
      ```
    </CodeGroup>
  </Step>

  <Step title="Start the batch job">
    Once your file is uploaded, create the batch job:

    <CodeGroup>
      ```python Python theme={null}
      batch = client.batches.create(
          input_file_id=input_file.id,
          endpoint="/v1/chat/completions",
          completion_window="24h",
          metadata={"description": "Evaluation run - December 2025"}
      )

      print(f"Batch started: {batch.id}")
      print(f"Status: {batch.status}")
      ```

      ```javascript Node.js theme={null}
      const batch = await client.batches.create({
        input_file_id: file.id,
        endpoint: "/v1/chat/completions",
        completion_window: "24h",
        metadata: { description: "Evaluation run - December 2025" }
      });

      console.log(`Batch started: ${batch.id}`);
      console.log(`Status: ${batch.status}`);
      ```

      ```bash cURL theme={null}
      curl https://api.cerebras.ai/v1/batches \
        -H "Authorization: Bearer $CEREBRAS_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
          "input_file_id": "file_abc123",
          "endpoint": "/v1/chat/completions",
          "completion_window": "24h",
          "metadata": {"description": "Evaluation run - December 2025"}
        }'
      ```
    </CodeGroup>

    The batch starts in `queued` status, then moves to `in_progress`, `finalizing`, and finally `completed`.
  </Step>

  <Step title="Track progress">
    Check on your batch job anytime to see how it's progressing:

    <CodeGroup>
      ```python Python theme={null}
      batch = client.batches.retrieve("batch_abc123")

      print(f"Status: {batch.status}")
      print(f"Completed: {batch.request_counts.completed}/{batch.request_counts.total}")
      ```

      ```javascript Node.js theme={null}
      const batch = await client.batches.retrieve("batch_abc123");

      console.log(`Status: ${batch.status}`);
      console.log(`Completed: ${batch.request_counts.completed}/${batch.request_counts.total}`);
      ```

      ```bash cURL theme={null}
      curl https://api.cerebras.ai/v1/batches/batch_abc123 \
        -H "Authorization: Bearer $CEREBRAS_API_KEY"
      ```
    </CodeGroup>

    The response includes detailed request count metrics showing how many requests have completed and failed.
  </Step>

  <Step title="Get your results">
    When the status shows `completed`, download your results:

    <CodeGroup>
      ```python Python theme={null}
      # Retrieve the result file
      results = client.batches.retrieve_results("batch_abc123")

      # Save locally
      with open("batch_results.jsonl", "wb") as f:
          f.write(results)
      ```

      ```javascript Node.js theme={null}
      const results = await client.batches.retrieveResults("batch_abc123");
      fs.writeFileSync("batch_results.jsonl", results);
      ```

      ```bash cURL theme={null}
      curl https://api.cerebras.ai/v1/batches/batch_abc123/results \
        -H "Authorization: Bearer $CEREBRAS_API_KEY" > batch_results.jsonl
      ```
    </CodeGroup>

    Your results file contains one line per request. Successful requests include the full completion response, while failed requests include error details:

    ```jsonl  theme={null}
    {"custom_id":"eval-001","status":"succeeded","response":{"id":"cmpl_1","object":"chat.completion","created":1699999999,"model":"llama-3.3-70b","choices":[{"index":0,"message":{"role":"assistant","content":"The water cycle consists of..."},"finish_reason":"stop"}],"usage":{"prompt_tokens":15,"completion_tokens":85,"total_tokens":100}}}
    {"custom_id":"eval-002","status":"succeeded","response":{"id":"cmpl_2","object":"chat.completion","created":1700000000,"model":"llama-3.3-70b","choices":[{"index":0,"message":{"role":"assistant","content":"Photosynthesis is the process..."},"finish_reason":"stop"}],"usage":{"prompt_tokens":12,"completion_tokens":92,"total_tokens":104}}}
    ```

    <Warning>
      Results aren't necessarily in the same order as your input. Always use `custom_id` to match requests to responses.
    </Warning>
  </Step>
</Steps>

## Batch States

Your batch progresses through these states:

| State         | What's happening                     |
| ------------- | ------------------------------------ |
| `queued`      | Waiting for processing capacity      |
| `in_progress` | Actively processing requests         |
| `finalizing`  | Preparing output file                |
| `completed`   | All done - results ready to download |
| `failed`      | System error prevented completion    |
| `expired`     | Exceeded 24-hour window              |
| `cancelled`   | You stopped the batch                |
| `cancelling`  | Cancellation in progress             |

Most batches complete well before the 24-hour limit, often within a few hours depending on size and load.

### Expired Batches

If your batch doesn't finish within 24 hours, unprocessed requests are marked as expired. You'll still get results for any completed requests, and expired ones appear in your output like this:

```json  theme={null}
{"custom_id":"eval-999","status":"expired","error":{"code":"timeout","message":"Batch expired before this request completed."}}
```

You're only charged for requests that completed.

## Cancel a Batch

Use the cancel endpoint:

<CodeGroup>
  ```python Python theme={null}
  cancelled = client.batches.cancel("batch_abc123")
  print(f"Status: {cancelled.status}")
  ```

  ```javascript Node.js theme={null}
  const cancelled = await client.batches.cancel("batch_abc123");
  console.log(`Status: ${cancelled.status}`);
  ```

  ```bash cURL theme={null}
  curl -X DELETE https://api.cerebras.ai/v1/batches/batch_abc123 \
    -H "Authorization: Bearer $CEREBRAS_API_KEY"
  ```
</CodeGroup>

Any completed requests remain available in your results. Unfinished requests will be deleted.

## Limits and Quotas

<AccordionGroup>
  <Accordion title="Batch size limits">
    * 50,000 requests maximum per batch
    * 200 MB maximum file size
    * 1 MB maximum per request line
  </Accordion>

  <Accordion title="Account limits">
    * 10 concurrent active batches
    * Configurable rate limits separate from real-time API
  </Accordion>

  <Accordion title="Storage">
    * Results retained for 7 days after completion
    * Automatic deletion after expiration (download promptly!)
  </Accordion>
</AccordionGroup>

## Organize Batches

Use `metadata` to keep track of different batch runs. Metadata is a set of key-value pairs that you can attach to a batch job for your own organizational purposes. For example, to track which environment, dataset, or version a batch belongs to.

```python  theme={null}
batch = client.batches.create(
    input_file_id="file_xyz",
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={
        "environment": "production",
        "dataset": "customer_feedback_q4",
        "version": "v2.1"
    }
)
```

The metadata you provide is stored with the batch object and returned in all API responses, making it easy to filter, search, and organize your batch jobs. Common uses include:

* **Environment tracking**: Tag batches with `production`, `staging`, or `development`
* **Dataset identification**: Link batches to specific datasets or experiments
* **Version control**: Track which version of your prompts or models you're testing

## Handling Large Datasets

Need to process more than 50,000 items? Split them across multiple batches:

```python  theme={null}
def split_into_batches(items, batch_size=50000):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

# Process each chunk as a separate batch
for i, chunk in enumerate(split_into_batches(all_items)):
    file = create_batch_file(chunk, f"batch_{i}.jsonl")
    # Submit each batch...
```


---

> To find navigation and other pages in this documentation, fetch the llms.txt file at: https://inference-docs.cerebras.ai/llms.txt