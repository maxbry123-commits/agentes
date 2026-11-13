# Intel NPU/GPU Profiling

## MatMul
```bash
./mm <device (npu/gpu/cpu)> <dtype (fp32/fp16/int8/int32)> <shape1> <shape2> <shape3>
```
INT8 matmul on NPU will raise an error, while it works well on GPU/CPU.

## MatMul weight as Constant
The only difference between this and the above is that the second input is Constant node of openvino.
```bash
./mm_const <device (npu/gpu/cpu)> <dtype (fp32/fp16/int8/int32)> <shape1> <shape2> <shape3>
```



## Throughput (with MatMul)
To reach peak throughput (TP), here we use matmul chain to increase data reuse and reduce I/O.
```bash
./mm_tp <device (npu/gpu/cpu) <dtype (fp32/fp16/int8/int32)> <shape_D> <mm_times>
```
In my tests, use `./mm_tp npu/gpu fp32 1024 500` achieves maximum TP, which is 2.7TFLOPS for NPU and 2.1TFLOPS for GPU.

## Throughput weight as constant(with MatMul)
The only difference between this and the above is that the weight is Constant node of openvino.
```bash
./mm_tp_const <device (npu/gpu/cpu) <dtype (fp32/fp16/int8/int32)> <shape_D> <mm_times>
```

## Matmul with changing weights
The difference between this and mm_tp is that it uses a changing weight each iteration.
```bash
./mm_var <device (npu/gpu/cpu) <dtype (fp32/fp16/int8/int32)> <shape_D> <mm_times>
```

## Matmul with changing weights
This is the same as above, but the weight is Constant node of openvino.
```bash
./mm_var_const <device (npu/gpu/cpu) <dtype (fp32/fp16/int8/int32)> <shape_D> <mm_times>
```