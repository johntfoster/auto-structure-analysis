"""Custom exception classes for the application."""


class AnalysisError(Exception):
    """Base exception for analysis-related errors."""
    pass


class DetectionError(AnalysisError):
    """Exception raised when structure detection fails."""
    pass


class CalibrationError(AnalysisError):
    """Exception raised when image calibration fails."""
    pass


class SolverError(AnalysisError):
    """Exception raised when FEA solver fails."""
    pass
