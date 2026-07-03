import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sqt_tool


class FakeTextWidget:
    def __init__(
        self,
        content: str,
        *,
        insert_index: str = "1.0",
        is_placeholder: bool = False,
    ) -> None:
        self.content = content
        self._is_placeholder = is_placeholder
        self._insert_index = insert_index

    def get(self, *_args: object) -> str:
        return self.content

    def delete(self, *_args: object) -> None:
        self.content = ""

    def insert(self, _index: str, value: str, *_tags: object) -> None:
        self.content = value

    def index(self, _index: object) -> str:
        return self._insert_index

    def mark_set(self, _mark: object, index: str) -> None:
        self._insert_index = index


class GenerateXmlContentTests(unittest.TestCase):
    def test_generate_xml_content_removes_invalid_xml_control_chars(self) -> None:
        content = sqt_tool.generate_xml_content(
            ["A\x00B"],
            sqt_tool.build_bracket_condition,
            "demo.nwd",
        )

        self.assertIn("AB", content)
        self.assertNotIn("\x00", content)


class LiveInputLimitTests(unittest.TestCase):
    def test_truncate_lines_for_input_clamps_each_line(self) -> None:
        over_limit = "A" * (sqt_tool.MAX_LINE_LENGTH + 3)
        second_over_limit = "B" * (sqt_tool.MAX_LINE_LENGTH + 2)
        truncated = sqt_tool._truncate_lines_for_input(
            f"{over_limit}\n{second_over_limit}\nok"
        )

        self.assertEqual(
            truncated,
            f'{"A" * sqt_tool.MAX_LINE_LENGTH}\n'
            f'{"B" * sqt_tool.MAX_LINE_LENGTH}\n'
            "ok",
        )

    def test_apply_live_line_limit_truncates_widget_content_and_cursor(self) -> None:
        over_limit = "1" * (sqt_tool.MAX_LINE_LENGTH + 3)
        text_widget = FakeTextWidget(
            f"{over_limit}\nok",
            insert_index=f"1.{sqt_tool.MAX_LINE_LENGTH + 3}",
        )

        changed = sqt_tool._apply_live_line_limit(text_widget)

        self.assertTrue(changed)
        self.assertEqual(
            text_widget.content,
            f'{"1" * sqt_tool.MAX_LINE_LENGTH}\nok',
        )
        self.assertEqual(text_widget.index(None), f"1.{sqt_tool.MAX_LINE_LENGTH}")

    def test_apply_live_line_limit_skips_placeholder_text(self) -> None:
        text_widget = FakeTextWidget(
            "输入内容",
            insert_index="1.4",
            is_placeholder=True,
        )

        changed = sqt_tool._apply_live_line_limit(text_widget)

        self.assertFalse(changed)
        self.assertEqual(text_widget.content, "输入内容")


class CoordinateTemplateTests(unittest.TestCase):
    def test_load_coordinate_template_info_reports_missing_template(self) -> None:
        with patch("sqt_tool.find_coordinate_template", return_value=None):
            template = sqt_tool.load_coordinate_template_info()

        self.assertEqual(template.filename, sqt_tool.DEFAULT_COORD_FILENAME)
        self.assertEqual(template.filepath, sqt_tool.DEFAULT_COORD_FILEPATH)
        self.assertIsNotNone(template.warning_message)

    def test_write_coordinate_xml_warns_when_defaults_are_used(self) -> None:
        output_path = Path("coordinate-output.xml").resolve()
        template = sqt_tool.CoordinateTemplateInfo(
            filename=sqt_tool.DEFAULT_COORD_FILENAME,
            filepath=sqt_tool.DEFAULT_COORD_FILEPATH,
            warning_message="模板缺失，已使用默认值。",
        )

        with (
            patch("sqt_tool.choose_save_path", return_value=str(output_path)),
            patch("sqt_tool.load_coordinate_template_info", return_value=template),
            patch("sqt_tool.write_xml_file") as mock_write,
            patch("sqt_tool.messagebox.showwarning") as mock_warning,
        ):
            sqt_tool.write_coordinate_xml(["X-01"])

        mock_write.assert_called_once()
        mock_warning.assert_called_once_with("模板提醒", template.warning_message)


class ErrorHandlingTests(unittest.TestCase):
    def test_write_bracket_xml_propagates_oserror_to_safe_submit(self) -> None:
        output_path = Path("bracket-output.xml").resolve()

        with (
            patch("sqt_tool.choose_save_path", return_value=str(output_path)),
            patch("sqt_tool.write_xml_file", side_effect=OSError("disk full")),
            patch("sqt_tool.messagebox.showerror") as mock_error,
        ):
            with self.assertRaisesRegex(OSError, "disk full"):
                sqt_tool.write_bracket_xml(["B-01"])

        mock_error.assert_not_called()

    def test_safe_submit_shows_write_error_from_handler(self) -> None:
        text_widget = SimpleNamespace(
            _is_placeholder=False,
            get=lambda *_args: "B-01\n",
        )
        root = SimpleNamespace(_input_text=text_widget)

        def handler(_items: list[str]) -> None:
            raise OSError("disk full")

        with patch("sqt_tool.messagebox.showerror") as mock_error:
            sqt_tool._safe_submit(root, handler)

        mock_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
