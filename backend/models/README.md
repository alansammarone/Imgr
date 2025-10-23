# SAM Model Checkpoints

Place the SAM model checkpoint file here.

## Download

Download `sam_vit_b_01ec64.pth` from the [Segment Anything Model repository](https://github.com/facebookresearch/segment-anything#model-checkpoints):

```bash
cd backend/models
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

Or use curl:

```bash
cd backend/models
curl -L -O https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

## Alternative Models

You can also use larger models for better quality:
- **ViT-L**: `sam_vit_l_0b3195.pth` (~1.2GB)
- **ViT-H**: `sam_vit_h_4b8939.pth` (~2.4GB)

If using a different model, set the `SAM_CHECKPOINT_PATH` environment variable to point to it.
