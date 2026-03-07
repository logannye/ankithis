"""Tests for rate limiting."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from ankithis_api.rate_limit import check_rate_limit


class TestRateLimit:
    def test_under_limit(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, None, 5, None]

        with patch("ankithis_api.rate_limit._get_redis", return_value=mock_redis):
            check_rate_limit("user-1", "upload", 10)

    def test_at_limit(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, None, 10, None]

        with patch("ankithis_api.rate_limit._get_redis", return_value=mock_redis):
            check_rate_limit("user-1", "upload", 10)

    def test_over_limit(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, None, 11, None]

        with patch("ankithis_api.rate_limit._get_redis", return_value=mock_redis):
            with pytest.raises(HTTPException) as exc_info:
                check_rate_limit("user-1", "upload", 10)
            assert exc_info.value.status_code == 429

    def test_pipeline_operations(self):
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, None, 1, None]

        with patch("ankithis_api.rate_limit._get_redis", return_value=mock_redis):
            check_rate_limit("user-1", "upload", 10)

        mock_pipe.zremrangebyscore.assert_called_once()
        mock_pipe.zadd.assert_called_once()
        mock_pipe.zcard.assert_called_once()
        mock_pipe.expire.assert_called_once()
