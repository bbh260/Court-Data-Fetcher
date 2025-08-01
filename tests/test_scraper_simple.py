import unittest
from unittest.mock import Mock, patch
import sys
import os
from bs4 import BeautifulSoup

# Add parent directory to path to import the scraper
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from delhi_court_scraper import DelhiCourtScraper


class TestDelhiCourtScraperBasic(unittest.TestCase):
    """Simple unit tests for Delhi Court Scraper core functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = DelhiCourtScraper()
    
    def test_scraper_initialization(self):
        """Test scraper initializes with correct URLs"""
        self.assertEqual(self.scraper.base_url, 'https://delhihighcourt.nic.in')
        self.assertEqual(self.scraper.case_search_url, 'https://delhihighcourt.nic.in/app/case-number')
        self.assertIsNotNone(self.scraper.session)
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        html = '<div>  Test   text  with\n  multiple   spaces  </div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        result = self.scraper._clean_text(element)
        self.assertEqual(result, 'Test text with multiple spaces')
    
    def test_extract_case_info_valid(self):
        """Test case info extraction with valid case number"""
        html = '<td>W.P.(C)-11180/2025</td>'
        soup = BeautifulSoup(html, 'html.parser')
        cell = soup.find('td')
        
        result = self.scraper._extract_case_info(cell)
        self.assertEqual(result['case_type'], 'W.P.(C)')
        self.assertEqual(result['case_number'], '11180')
        self.assertEqual(result['year'], '2025')
    
    def test_extract_case_info_invalid(self):
        """Test case info extraction with invalid format"""
        html = '<td>Invalid format</td>'
        soup = BeautifulSoup(html, 'html.parser')
        cell = soup.find('td')
        
        result = self.scraper._extract_case_info(cell)
        self.assertEqual(result['case_type'], 'NA')
        self.assertEqual(result['case_number'], 'NA')
        self.assertEqual(result['year'], 'NA')
    
    def test_extract_parties_with_vs(self):
        """Test party extraction with VS separator"""
        html = '<td>ANIJAY TYAGI VS MUNICIPAL CORPORATION</td>'
        soup = BeautifulSoup(html, 'html.parser')
        cell = soup.find('td')
        
        result = self.scraper._extract_parties(cell)
        self.assertEqual(result['petitioner'], 'ANIJAY TYAGI')
        self.assertEqual(result['respondent'], 'MUNICIPAL CORPORATION')
    
    def test_extract_parties_without_vs(self):
        """Test party extraction without VS separator"""
        html = '<td>PETITIONER NAME ONLY</td>'
        soup = BeautifulSoup(html, 'html.parser')
        cell = soup.find('td')
        
        result = self.scraper._extract_parties(cell)
        self.assertEqual(result['petitioner'], 'PETITIONER NAME ONLY')
        self.assertEqual(result['respondent'], 'NA')
    
    def test_is_case_results_table_valid(self):
        """Test case results table detection with valid table"""
        html = '''
        <table>
            <tr><th>Case No</th><th>Party</th></tr>
            <tr><td>W.P.(C)-123/2025</td><td>John vs Jane</td></tr>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        self.assertTrue(self.scraper._is_case_results_table(table))
    
    def test_is_case_results_table_invalid(self):
        """Test case results table detection with invalid table"""
        html = '''
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>John</td><td>30</td></tr>
        </table>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        self.assertFalse(self.scraper._is_case_results_table(table))
    
    def test_extract_captcha_and_token_success(self):
        """Test CAPTCHA and token extraction with valid HTML"""
        html = '''
        <html>
            <body>
                <span id="captcha-code">ABC123</span>
                <input type="hidden" name="_token" value="test_token_value">
            </body>
        </html>
        '''
        mock_response = Mock()
        mock_response.text = html
        
        captcha, token = self.scraper._step2_extract_captcha_and_token(mock_response)
        
        self.assertEqual(captcha, 'ABC123')
        self.assertEqual(token, 'test_token_value')
    
    def test_extract_captcha_and_token_missing(self):
        """Test CAPTCHA and token extraction with missing elements"""
        html = '<html><body><p>No captcha here</p></body></html>'
        mock_response = Mock()
        mock_response.text = html
        
        captcha, token = self.scraper._step2_extract_captcha_and_token(mock_response)
        
        self.assertIsNone(captcha)
        self.assertIsNone(token)
    
    def test_parse_results_no_results_message(self):
        """Test result parsing when no cases found"""
        html = '''
        <html>
            <body>
                <p>No case found for the given criteria</p>
            </body>
        </html>
        '''
        mock_response = Mock()
        mock_response.text = html
        
        result = self.scraper._step5_parse_results(mock_response)
        
        self.assertIn('error', result)
        self.assertIn('no case found', result['error'].lower())


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
