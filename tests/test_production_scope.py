import unittest

from scripts.production_scope_core import (
    ChapterRange,
    compute_forward_index_range,
    compute_required_cumulative_index_range,
    parse_scope_choice,
    should_ask_scope_gate,
)


class ProductionScopeCoreTests(unittest.TestCase):
    def test_ambiguous_long_formal_request_requires_scope_gate(self) -> None:
        decision = should_ask_scope_gate(
            total_chapters=12,
            explicit_output_range=None,
            is_formal_production=True,
        )

        self.assertTrue(decision.required)
        self.assertEqual(decision.recommended_chapters, 3)
        self.assertIn("建议先跑3章", decision.prompt)
        self.assertIn("收到选择前，我不会生成连续投喂稿或复制包", decision.prompt)

    def test_three_or_fewer_chapters_do_not_require_scope_gate(self) -> None:
        decision = should_ask_scope_gate(
            total_chapters=3,
            explicit_output_range=None,
            is_formal_production=True,
        )

        self.assertFalse(decision.required)
        self.assertEqual(decision.recommended_chapters, 3)

    def test_explicit_one_chapter_delivers_one_and_reads_next_three(self) -> None:
        output_range = parse_scope_choice("跑第1章", total_chapters=8, gate_was_shown=False)
        forward_range = compute_forward_index_range(output_range, total_chapters=8)

        self.assertEqual(output_range, ChapterRange(1, 1))
        self.assertEqual(forward_range, ChapterRange(1, 4))

    def test_default_after_gate_means_first_three_chapters(self) -> None:
        output_range = parse_scope_choice("默认", total_chapters=10, gate_was_shown=True)
        forward_range = compute_forward_index_range(output_range, total_chapters=10)

        self.assertEqual(output_range, ChapterRange(1, 3))
        self.assertEqual(forward_range, ChapterRange(1, 6))

    def test_specific_range_expands_cumulative_index_without_dropping_old_range(self) -> None:
        output_range = parse_scope_choice("跑第2-3章", total_chapters=9, gate_was_shown=False)
        forward_range = compute_forward_index_range(output_range, total_chapters=9)
        cumulative_range = compute_required_cumulative_index_range(
            existing_index_range=ChapterRange(1, 4),
            forward_index_range=forward_range,
        )

        self.assertEqual(output_range, ChapterRange(2, 3))
        self.assertEqual(forward_range, ChapterRange(2, 6))
        self.assertEqual(cumulative_range, ChapterRange(1, 6))

    def test_full_book_batch_default_is_three_chapters(self) -> None:
        output_range = parse_scope_choice("全本分批", total_chapters=20, gate_was_shown=True)

        self.assertEqual(output_range, ChapterRange(1, 3))

    def test_full_book_batch_requires_scope_gate_to_have_been_shown(self) -> None:
        with self.assertRaises(ValueError):
            parse_scope_choice("全本分批", total_chapters=20, gate_was_shown=False)

    def test_count_choice_means_first_n_chapters_not_specific_chapter_n(self) -> None:
        for text in ("跑3章", "先跑3章"):
            with self.subTest(text=text):
                output_range = parse_scope_choice(text, total_chapters=20, gate_was_shown=True)

                self.assertEqual(output_range, ChapterRange(1, 3))

    def test_try_one_chapter_phrase_means_first_chapter(self) -> None:
        output_range = parse_scope_choice("先试一章", total_chapters=20, gate_was_shown=True)

        self.assertEqual(output_range, ChapterRange(1, 1))


if __name__ == "__main__":
    unittest.main()
