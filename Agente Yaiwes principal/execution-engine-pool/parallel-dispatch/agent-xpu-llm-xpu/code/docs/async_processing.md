# Asynchronous Job Processing

This document describes the asynchronous job processing system implemented in `ContextOV` for handling concurrent inference requests from multiple clients.

## Overview

The async processing system consists of two event loops:

1. **Prefill Event Loop**: Processes single jobs through all model layers during the prefill stage
2. **Decode Event Loop**: Processes batched jobs through decode iterations

## Architecture

### Key Components

- **Job Queues**: Thread-safe queues for prefill and decode stages
- **Event Loops**: Dedicated threads for processing jobs asynchronously
- **Job Lifecycle**: Jobs transition from prefill → decode → completion
- **Batching**: Decode phase batches up to `MAX_DECODE_BATCH_SIZE_` jobs for efficiency

### Thread Safety

- All queue operations are protected by mutexes
- Condition variables coordinate between producer (job submission) and consumers (event loops)
- Atomic flags control the lifecycle of event loops

## Usage

### Starting Async Processing

```cpp
ContextOV context(model_path);
context.start_async_processing();
```

### Submitting Jobs

```cpp
// Create and configure job
InferJob job = create_infer_job("unique_id");
job->prompt_tokens = {1, 2, 3, 4, 5};
job->prompt_len = job->prompt_tokens.size();
job->temperature = 0.7f;
job->top_p = 0.9f;
job->seed = 42;

// Define completion callback (optional)
auto callback = [](InferJob completed_job) {
    std::cout << "Job " << completed_job->uuid << " completed with " 
              << completed_job->generated_tokens.size() << " tokens" << std::endl;
};

// Submit job
context.submit_job(job, callback);
```

### Stopping Async Processing

```cpp
context.stop_async_processing();
```

## Event Loop Details

### Prefill Event Loop

1. Waits for jobs in the prefill queue
2. Processes one job at a time through all model layers:
   - `prefill_job_swapin()`
   - For each layer: `proceed_pre_attn_prefill()` → `proceed_attn_prefill()` → `proceed_post_attn_prefill()`
   - `proceed_final_out_prefill()`
   - `prefill_job_swapout()`
3. Moves completed prefill jobs to the decode queue

### Decode Event Loop

1. Collects jobs from decode queue (up to batch size limit)
2. Processes the batch through decode iterations:
   - `decode_job_batch_swapin()`
   - For each layer: `proceed_pre_attn_decode()` → `proceed_attn_decode()` → `proceed_post_attn_decode()`
   - `proceed_final_out_decode()`
   - `decode_job_batch_swapout()`
3. Continues until jobs complete (end token, context limit, or max steps)
4. Calls completion callbacks for finished jobs

## Job Completion Conditions

Jobs complete when any of the following occur:

1. **End of Generation Token**: Model generates an end-of-sequence token
2. **Context Length Limit**: Job reaches maximum context length
3. **Token Position Limit**: Job exceeds absolute token position limit
4. **Error Condition**: Exception during processing

## Performance Considerations

### Batching Strategy

- Decode phase batches jobs for GPU efficiency
- Batch size limited by `MAX_DECODE_BATCH_SIZE_` (default: 32)
- Jobs with different generation lengths can be processed together

### Resource Management

- KV cache allocated automatically for each job
- Memory released when jobs complete
- Event loops run continuously but block when no work available

### Throughput Optimization

- Prefill processes one job at a time (memory-intensive)
- Decode batches multiple jobs (compute-intensive)
- Pipeline allows prefill and decode to run concurrently

## Error Handling

- Exceptions in event loops are caught and logged
- Failed jobs are completed with error status
- Event loops continue processing other jobs after errors
- Graceful shutdown ensures all threads terminate properly

## Example Integration

See `async_example.cc` for a complete example of using the async processing system.

## Thread Model

```
Main Thread
├── Prefill Thread (prefill_event_loop)
│   └── Processes jobs sequentially through all layers
└── Decode Thread (decode_event_loop)
    └── Processes job batches through decode iterations
```

This design allows for maximum throughput by:
- Overlapping prefill and decode processing
- Batching decode operations for efficiency
- Minimizing thread synchronization overhead