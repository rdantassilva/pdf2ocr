import platform
import pytest
from unittest.mock import patch
from pdf2ocr.utils import detect_package_manager, check_dependencies

def test_detect_package_manager_darwin():
    """Test package manager detection on macOS"""
    with patch('platform.system', return_value='Darwin'):
        assert detect_package_manager() == 'brew'

def test_detect_package_manager_linux_apt():
    """Test package manager detection on Linux with apt"""
    with patch('platform.system', return_value='Linux'):
        with patch('shutil.which', side_effect=lambda x: x == 'apt'):
            assert detect_package_manager() == 'apt'

def test_detect_package_manager_linux_dnf():
    """Test package manager detection on Linux with dnf"""
    with patch('platform.system', return_value='Linux'):
        with patch('shutil.which', side_effect=lambda x: x == 'dnf'):
            assert detect_package_manager() == 'dnf'

def test_detect_package_manager_linux_yum():
    """Test package manager detection on Linux with yum"""
    with patch('platform.system', return_value='Linux'):
        with patch('shutil.which', side_effect=lambda x: x == 'yum'):
            assert detect_package_manager() == 'yum'

def test_detect_package_manager_unknown():
    """Test package manager detection on unknown system"""
    with patch('platform.system', return_value='Windows'):
        assert detect_package_manager() is None

def test_check_dependencies_all_present():
    """Test dependency checking when all dependencies are present"""
    with patch('shutil.which', return_value='/usr/bin/tesseract'):
        # Should not raise any exception
        check_dependencies(generate_epub=False)

def test_check_dependencies_missing_tesseract():
    """Test dependency checking when tesseract is missing"""
    def mock_which(cmd):
        return None if cmd == 'tesseract' else '/usr/bin/' + cmd
    
    with patch('shutil.which', side_effect=mock_which):
        with pytest.raises(SystemExit):
            check_dependencies(generate_epub=False)

def test_check_dependencies_missing_pdftoppm():
    """Test dependency checking when pdftoppm is missing"""
    def mock_which(cmd):
        return None if cmd == 'pdftoppm' else '/usr/bin/' + cmd
    
    with patch('shutil.which', side_effect=mock_which):
        with pytest.raises(SystemExit):
            check_dependencies(generate_epub=False)

def test_check_dependencies_missing_calibre():
    """Test dependency checking when calibre is missing but not required"""
    def mock_which(cmd):
        return None if cmd == 'ebook-convert' else '/usr/bin/' + cmd
    
    with patch('shutil.which', side_effect=mock_which):
        # Should not raise any exception since epub generation is not requested
        check_dependencies(generate_epub=False)

def test_check_dependencies_missing_calibre_required():
    """Test dependency checking when calibre is missing and required"""
    def mock_which(cmd):
        return None if cmd == 'ebook-convert' else '/usr/bin/' + cmd
    
    with patch('shutil.which', side_effect=mock_which):
        with pytest.raises(SystemExit):
            check_dependencies(generate_epub=True) 