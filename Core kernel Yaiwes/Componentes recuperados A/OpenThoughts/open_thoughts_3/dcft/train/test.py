import torch

print("Torch version:", torch.__version__)

# Check if CUDA is available
if torch.cuda.is_available():
    print("CUDA is available")
    print("GPU Name:", torch.cuda.get_device_name(0))
    print("CUDA Version:", torch.version.cuda)
else:
    print("CUDA is NOT available, using CPU")

# Simple tensor operation
try:
    x = torch.tensor([1.0, 2.0, 3.0])
    y = x.to("cuda") if torch.cuda.is_available() else x.to("cpu")
    print("Tensor operation successful:", y)
except Exception as e:
    print("Error during tensor operation:", e)
