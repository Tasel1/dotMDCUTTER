import os
import tempfile
from dotmdcutter.cli import run_cli


def test_cli_help():
    # Should exit with code 0 on --help
    try:
        run_cli(["--help"])
    except SystemExit as e:
        assert e.code == 0


def test_cli_export():
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_md = os.path.join(tmp_dir, "notes.md")
        out_slices = os.path.join(tmp_dir, "output_imgs")
        with open(input_md, "w", encoding="utf-8") as f:
            f.write("# Тестовые заметки\nПараграф 1\n---page---\nПараграф 2\n")

        ret = run_cli(
            [
                input_md,
                "-o",
                out_slices,
                "-w",
                "320",
                "-H",
                "240",
                "-t",
                "dark",
                "-f",
                "png",
            ]
        )
        assert ret == 0

        created = sorted(os.listdir(out_slices))
        assert len(created) == 2
        assert created[0].endswith(".png")
        assert created[1].endswith(".png")


def test_cli_orientation_flag():
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_md = os.path.join(tmp_dir, "portrait.md")
        out_slices = os.path.join(tmp_dir, "portrait_imgs")
        with open(input_md, "w", encoding="utf-8") as f:
            f.write("# Портрет\nТекст")

        ret = run_cli(
            [
                input_md,
                "-o",
                out_slices,
                "--orientation",
                "portrait",
                "-f",
                "jpg",
            ]
        )
        assert ret == 0

        from PIL import Image

        files = os.listdir(out_slices)
        assert len(files) == 1
        with Image.open(os.path.join(out_slices, files[0])) as img:
            assert img.size == (240, 320)


def test_cli_scale_flag():
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_md = os.path.join(tmp_dir, "scaled.md")
        out_slices = os.path.join(tmp_dir, "scaled_imgs")
        with open(input_md, "w", encoding="utf-8") as f:
            f.write("# Масштаб 2x\nЧеткий текст.")

        ret = run_cli(
            [
                input_md,
                "-o",
                out_slices,
                "-s",
                "2",
                "-w",
                "320",
                "-H",
                "240",
            ]
        )
        assert ret == 0

        from PIL import Image

        files = os.listdir(out_slices)
        assert len(files) == 1
        with Image.open(os.path.join(out_slices, files[0])) as img:
            assert img.size == (640, 480)
