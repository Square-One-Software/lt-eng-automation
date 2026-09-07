"""Tests for translate_to_chinese function."""
import unittest
from unittest.mock import patch, MagicMock
from utils import translate_to_chinese, create_vocabulary_table
from deep_translator.exceptions import TooManyRequests, RequestError, TranslationNotFound
import requests


class TestTranslateToChinese(unittest.TestCase):
    """Unit tests for translate_to_chinese."""

    @patch('utils.GoogleTranslator')
    def test_successful_translation(self, mock_translator_class):
        """Test successful translation returns result."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "你好"
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=1)
        
        self.assertEqual(result, "你好")
        mock_translator.translate.assert_called_once_with("hello")

    @patch('utils.GoogleTranslator')
    @patch('utils.time.sleep')
    def test_retry_on_rate_limit(self, mock_sleep, mock_translator_class):
        """Test retry logic on TooManyRequests (rate limiting)."""
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = [
            TooManyRequests(),
            TooManyRequests(),
            "你好"
        ]
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3)
        
        self.assertEqual(result, "你好")
        self.assertEqual(mock_translator.translate.call_count, 3)
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch('utils.GoogleTranslator')
    @patch('utils.time.sleep')
    def test_retry_on_network_error(self, mock_sleep, mock_translator_class):
        """Test retry logic on RequestError (network errors)."""
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = [
            RequestError(),
            "你好"
        ]
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3)
        
        self.assertEqual(result, "你好")
        self.assertEqual(mock_translator.translate.call_count, 2)

    @patch('utils.GoogleTranslator')
    def test_returns_original_on_translation_not_found(self, mock_translator_class):
        """Test returns original text when TranslationNotFound (non-retryable)."""
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = TranslationNotFound("test")
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3)
        
        self.assertEqual(result, "hello")
        mock_translator.translate.assert_called_once()

    @patch('utils.GoogleTranslator')
    @patch('utils.time.sleep')
    def test_returns_original_after_max_retries(self, mock_sleep, mock_translator_class):
        """Test returns original text after exhausting retries."""
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = TooManyRequests()
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3)
        
        self.assertEqual(result, "hello")
        self.assertEqual(mock_translator.translate.call_count, 3)

    @patch('utils.GoogleTranslator')
    @patch('utils.time.sleep')
    def test_returns_original_on_requests_exception(self, mock_sleep, mock_translator_class):
        """Test handles requests.exceptions.RequestException."""
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = requests.exceptions.ConnectionError()
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3)
        
        self.assertEqual(result, "hello")
        self.assertEqual(mock_translator.translate.call_count, 3)

    @patch('utils.GoogleTranslator')
    @patch('utils.time.sleep')
    def test_delay_between_successful_translations(self, mock_sleep, mock_translator_class):
        """Test delay is applied after successful translation."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "你好"
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3, base_delay=0.5)
        
        self.assertEqual(result, "你好")
        mock_sleep.assert_called_with(0.5)

    @patch('utils.GoogleTranslator')
    def test_unexpected_exception_returns_original(self, mock_translator_class):
        """Test unexpected exceptions return original text without retry."""
        mock_translator = MagicMock()
        mock_translator.translate.side_effect = ValueError("unexpected")
        mock_translator_class.return_value = mock_translator
        
        result = translate_to_chinese("hello", max_retries=3)
        
        self.assertEqual(result, "hello")
        mock_translator.translate.assert_called_once()


class TestCreateVocabularyTable(unittest.TestCase):
    """Tests for create_vocabulary_table."""

    @patch('utils.translate_to_chinese')
    def test_creates_table_structure(self, mock_translate):
        """Test table has correct structure."""
        mock_translate.return_value = "你好"
        
        vocab_data = [
            ("hello", "n.", ""),
            ("world", "n.", "")
        ]
        
        result = create_vocabulary_table(vocab_data)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ['Vocabulary (Part of Speech)', 'Chinese Meaning'])
        self.assertEqual(result[1], ['hello (n.)', '你好'])
        self.assertEqual(result[2], ['world (n.)', '你好'])

    @patch('utils.translate_to_chinese')
    def test_uses_custom_meaning_when_provided(self, mock_translate):
        """Test custom meaning takes precedence over translation."""
        mock_translate.return_value = "你好"
        
        vocab_data = [
            ("hello", "n.", "自訂意思")
        ]
        
        result = create_vocabulary_table(vocab_data)
        
        self.assertEqual(result[1], ['hello (n.)', '自訂意思'])
        mock_translate.assert_called_once_with("hello")


class TestIntegration(unittest.TestCase):
    """Integration tests (requires network)."""

    def test_real_translation(self):
        """Test real translation (slow, requires network)."""
        result = translate_to_chinese("hello", max_retries=1)
        self.assertIsInstance(result, str)
        self.assertIn(result, ["hello", "你好", "您好", "哈囉"])

    def test_real_vocabulary_table(self):
        """Test real vocabulary table creation (slow, requires network)."""
        vocab_data = [
            ("cat", "n.", ""),
            ("dog", "n.", "")
        ]
        result = create_vocabulary_table(vocab_data)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ['Vocabulary (Part of Speech)', 'Chinese Meaning'])


if __name__ == '__main__':
    unittest.main()
