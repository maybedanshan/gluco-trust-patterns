import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from verify_release import verify


class ArchiveTests(unittest.TestCase):
    def test_complete_manifest_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'release.zip'
            content=b'example source'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('project/README.md',content)
                z.writestr('project/MANIFEST.sha256',hashlib.sha256(content).hexdigest()+'  README.md\n')
            checksum=path.with_suffix('.zip.sha256')
            checksum.write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  release.zip\n')
            self.assertEqual(verify(path)[0],1)
            with zipfile.ZipFile(path,'a') as z:z.writestr('project/unlisted.txt','extra')
            with self.assertRaisesRegex(ValueError,'Archive checksum'):verify(path)
            checksum.write_text(hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,'Manifest'):verify(path)


if __name__=='__main__':unittest.main()
