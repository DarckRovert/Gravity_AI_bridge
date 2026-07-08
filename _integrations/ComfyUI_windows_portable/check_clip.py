import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.insert(0, r'F:\Gravity_AI_bridge\_integrations\ComfyUI_windows_portable\ComfyUI')
import comfy.sd

ckpt = comfy.sd.load_checkpoint_guess_config(
    r'F:\Gravity_AI_bridge\_integrations\ComfyUI_windows_portable\ComfyUI\models\checkpoints\ltx-video-2b-v0.9.5.safetensors',
    output_vae=True, output_clip=True
)
model, clip, vae, _ = ckpt
print('CLIP type:', type(clip).__name__ if clip else 'None')
if clip is not None:
    print('cond_stage_model:', type(clip.cond_stage_model).__name__)
    try:
        tokens = clip.tokenizer.tokenize_with_weights('test')
        print('Tokenizer ok, tokens keys:', list(tokens.keys()) if isinstance(tokens, dict) else type(tokens).__name__)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        print('Cond shape:', cond.shape, '| dim:', cond.shape[-1])
    except Exception as e:
        print('Encode error:', e)
