"""analyser 模块单元测试"""
import os
from unittest.mock import patch, MagicMock

import pytest

from analysis.analyser import create_client, analyse_user


def test_create_client_no_key():
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            create_client()


def test_create_client_with_key():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("analysis.analyser.OpenAI") as mock_openai:
            client = create_client()
            mock_openai.assert_called_once_with(api_key="test-key")


def test_analyse_user():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="# 测试报告\n\n分析结果"))]
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("analysis.analyser.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            result = analyse_user("测试上下文")
            assert "测试报告" in result
            mock_client.chat.completions.create.assert_called_once()
