"""Integration tests: real media inputs and encoder, no remote services/mocks.
Breaks caught: stretched/cropped source, missing narration/captions, wrong ratio,
silent acceptance of missing assets, unintended outbound/provider calls.
"""
import json,os,shutil,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
LOCAL_FFMPEG=HERE.parents[3]/'work/useme-pakiet35-2026-10-11/vendor/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
FFMPEG=Path(os.environ.get('FFMPEG_EXE') or shutil.which('ffmpeg') or LOCAL_FFMPEG)

class RealWorkflowTest(unittest.TestCase):
    def test_video_input_is_decoded_instead_of_being_ignored(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            root=Path(temp);Image.new('RGB',(400,200),'white').save(root/'fallback.png')
            subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-f','lavfi','-i','testsrc2=size=400x200:rate=24','-t','1','-pix_fmt','yuv420p',str(root/'motion.mp4')],check=True)
            with wave.open(str(root/'voice.wav'),'wb') as audio:
                audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000);audio.writeframes(b'\x20\x03'*16000)
            (root/'job.json').write_text(json.dumps({'image':'fallback.png','video':'motion.mp4','audio':'voice.wav','duration':1,'headline':'Ruch źródła','caption':'Zachowane klatki.','cta':'Dalej'}),encoding='utf-8')
            run=subprocess.run([sys.executable,str(HERE/'workflow.py'),'--job',str(root/'job.json'),'--output',str(root/'out'),'--preset','editorial','--ratio','16:9','--size','360','--ffmpeg',str(FFMPEG)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            manifest=json.loads((root/'out/manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest.get('source_video_frames_decoded',0),24)
            self.assertIn('video',manifest['source'])
            self.assertEqual(manifest['product_geometry']['source_dimensions'],[400,200])

    def test_render_preserves_product_and_has_audio_and_captions(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            root=Path(temp); image=Image.new('RGB',(400,200),'white')
            # Hand-derived aspect ratio 2:1. A red marker exposes cropping.
            for x in range(10):
                for y in range(200):image.putpixel((x,y),(230,20,30))
            image.save(root/'product.png')
            with wave.open(str(root/'voice.wav'),'wb') as audio:
                audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000)
                audio.writeframes(b'\x20\x03'*16000)
            job={'image':'product.png','audio':'voice.wav','duration':1.0,'headline':'Autorski produkt','caption':'Ten sam kształt.','source_kind':'own_fixture','audio_kind':'test_tone','cta':'Zobacz szczegóły'}
            (root/'job.json').write_text(json.dumps(job),encoding='utf-8')
            run=subprocess.run([sys.executable,str(HERE/'workflow.py'),'--job',str(root/'job.json'),'--output',str(root/'out'),'--preset','product-focus','--ratio','9:16','--size','360','--ffmpeg',str(FFMPEG)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            manifest=json.loads((root/'out/manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['output']['dimensions'],[360,640])
            self.assertTrue(manifest['output']['audio_present'])
            self.assertEqual(manifest['product_geometry']['source_aspect_ratio'],2.0)
            box=manifest['product_geometry']['image_box']
            self.assertAlmostEqual(box[2]/box[3],2.0,delta=.01)
            self.assertEqual(manifest['network_calls'],0)
            self.assertFalse(manifest['llm_called'])
            self.assertTrue((root/'out/captions.srt').read_text(encoding='utf-8').strip().endswith('Ten sam kształt.'))
            self.assertGreater((root/'out/video.mp4').stat().st_size,2000)

    def test_missing_asset_fails_without_output(self):
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            root=Path(temp);(root/'job.json').write_text(json.dumps({'image':'missing.png','audio':'missing.wav','duration':1,'headline':'X','caption':'Y','cta':'Z'}),encoding='utf-8')
            run=subprocess.run([sys.executable,str(HERE/'workflow.py'),'--job',str(root/'job.json'),'--output',str(root/'out'),'--preset','product-focus','--ratio','9:16','--size','360','--ffmpeg',str(FFMPEG)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('Missing source',run.stderr)
            self.assertFalse((root/'out').exists())

if __name__=='__main__':unittest.main(verbosity=2)
