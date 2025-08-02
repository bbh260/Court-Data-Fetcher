import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
import re
import json
from urllib.parse import urljoin, urlparse

class DelhiCourtScraper:
    """
    1. Access the site and create session
    2. Extract captcha code and _token
    3. Validate captcha
    4. Submit case search
    5. Parse results table
    """
    
    def __init__(self):
        self.base_url = 'https://delhihighcourt.nic.in'
        self.case_search_url = f'{self.base_url}/app/case-number'
        self.validate_captcha_url = f'{self.base_url}/app/validateCaptcha'
        
        # Create session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        self.logger = logging.getLogger(__name__)
        
    def search_case(self, case_type, case_number, year):
        """
        Complete case search following the 5-step process
        
        Args:
            case_type (str): Case type like 'CRLMM', 'WP(C)', etc.
            case_number (str): Case number like '558'
            year (str): Year like '2025'
            
        Returns:
            dict: Contains case data or error information
        """
        try:
            self.logger.info(f"Starting case search for {case_type} {case_number}/{year}")
            
            # Step 1: Create session and access the site
            initial_response = self._step1_access_site()
            if not initial_response:
                return {'error': 'Failed to access initial site'}
            
            # Step 2: Parse HTML and extract captcha code and token
            captcha_code, token = self._step2_extract_captcha_and_token(initial_response)
            if not captcha_code or not token:
                return {'error': 'Failed to extract captcha code or token'}
            
            self.logger.info(f"Extracted captcha: {captcha_code}, token: {token[:20]}...")
            
            # Step 3: Validate captcha
            if not self._step3_validate_captcha(token, captcha_code):
                return {'error': 'Failed to validate captcha'}
            
            # Step 4: Submit case search
            search_response = self._step4_submit_case_search(token, case_type, case_number, year, captcha_code)
            if not search_response:
                return {'error': 'Failed to submit case search'}
            
            # Step 5: Parse results table
            case_data = self._step5_parse_results(search_response)
            
            return {
                'success': True,
                'case_type': case_type,
                'case_number': case_number,
                'year': year,
                'data': case_data
            }
            
        except Exception as e:
            self.logger.error(f"Error in case search: {str(e)}")
            return {'error': f'Search failed: {str(e)}'}
    
    def _step1_access_site(self):
        """Step 1: Create session and access the site"""
        try:
            self.logger.info("Step 1: Accessing case search page")
            response = self.session.get(self.case_search_url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Step 1 failed: {str(e)}")
            return None
    
    def _step2_extract_captcha_and_token(self, response):
        """Step 2: Parse HTML and extract captcha code and _token"""
        try:
            self.logger.info("Step 2: Extracting captcha code and token")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract captcha code from span with id 'captcha-code'
            captcha_element = soup.find('span', {'id': 'captcha-code'})
            if not captcha_element:
                self.logger.error("Captcha code element not found")
                return None, None
            
            captcha_code = captcha_element.get_text(strip=True)
            
            # Extract token from hidden input
            token_element = soup.find('input', {'name': '_token', 'type': 'hidden'})
            if not token_element:
                self.logger.error("Token element not found")
                return None, None
            
            token = token_element.get('value')
            
            return captcha_code, token
            
        except Exception as e:
            self.logger.error(f"Step 2 failed: {str(e)}")
            return None, None
    
    def _step3_validate_captcha(self, token, captcha_code):
        """Step 3: Validate captcha using XMLHttpRequest"""
        try:
            self.logger.info("Step 3: Validating captcha")
            
            headers = {
                'Host': 'delhihighcourt.nic.in',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Origin': 'https://delhihighcourt.nic.in',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': 'https://delhihighcourt.nic.in/app/case-number',
                'Priority': 'u=1, i'
            }
            
            data = {
                '_token': token,
                'captchaInput': captcha_code
            }
            
            response = self.session.post(
                self.validate_captcha_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            # Check if validation was successful
            return response.status_code == 200
            
        except requests.RequestException as e:
            self.logger.error(f"Step 3 failed: {str(e)}")
            return False
    
    def _step4_submit_case_search(self, token, case_type, case_number, year, captcha_code):
        """Step 4: Submit case search form"""
        try:
            self.logger.info("Step 4: Submitting case search")
            
            headers = {
                'Host': 'delhihighcourt.nic.in',
                'Cache-Control': 'max-age=0',
                'Origin': 'https://delhihighcourt.nic.in',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Upgrade-Insecure-Requests': '1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Dest': 'document',
                'Referer': 'https://delhihighcourt.nic.in/app/case-number',
                'Priority': 'u=0, i'
            }
            
            data = {
                '_token': token,
                'case_type': case_type,
                'case_number': case_number,
                'year': year,
                'randomid': captcha_code,
                'captchaInput': captcha_code
            }
            
            response = self.session.post(
                self.case_search_url,
                headers=headers,
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"Step 4 failed: {str(e)}")
            return None
    
    def _step5_parse_results(self, response):
        """Step 5: Parse the results table and return standardized format"""
        try:
            self.logger.info("Step 5: Parsing results table")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for common "no results" messages
            page_text = soup.get_text().lower()
            no_results_indicators = [
                'no case found', 'no cases found', 'no record found', 
                'no records found', 'case not found', 'no result found',
                'no data found', 'record not available'
            ]
            
            for indicator in no_results_indicators:
                if indicator in page_text:
                    self.logger.warning(f"Found 'no results' indicator: '{indicator}'")
                    return {'error': f'No case results found - website returned: {indicator}'}
            
            # Try to find judgment table first (pattern 1)
            judgment_table = soup.find('table', {'id': 's_judgeTable'})
            if judgment_table:
                return self._parse_judgment_table_standardized(judgment_table)
            
            # Try to find case table (pattern 2)
            case_table = soup.find('table', {'id': 'caseTable'})
            if case_table:
                return self._parse_case_table_standardized(case_table)
            
            # Try to find any table with case data
            tables = soup.find_all('table', class_=['table', 'table-hover', 'table-bordered'])
            
            for table in tables:
                if self._is_case_results_table(table):
                    return self._parse_generic_case_table_standardized(table)
            
            self.logger.warning("No case results table found")
            return {'error': 'No case results found - no recognizable data tables in response'}
            
        except Exception as e:
            self.logger.error(f"Step 5 failed: {str(e)}")
            return {'error': f'Failed to parse results: {str(e)}'}
    
    def _parse_judgment_table(self, table):
        """Parse judgment table (pattern 1) - s_judgeTable"""
        try:
            cases = []
            tbody = table.find('tbody')
            if not tbody:
                return {'error': 'No tbody found in judgment table'}
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 5:
                    case_data = {
                        'serial_no': cells[0].get_text(strip=True),
                        'case_no': self._extract_case_number_with_dhc(cells[1]),
                        'judgment_date': self._extract_judgment_links(cells[2]),
                        'parties': self._clean_text(cells[3]).replace('&nbsp', ' '),
                        'corrigendum': self._clean_text(cells[4]).replace('&nbsp', ' ')
                    }
                    cases.append(case_data)
            
            return {'cases': cases, 'table_type': 'judgment'}
            
        except Exception as e:
            self.logger.error(f"Error parsing judgment table: {str(e)}")
            return {'error': f'Failed to parse judgment table: {str(e)}'}
    
    def _parse_case_table(self, table):
        """Parse case table (pattern 2) - caseTable"""
        try:
            cases = []
            tbody = table.find('tbody')
            if not tbody:
                return {'error': 'No tbody found in case table'}
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 4:
                    case_data = {
                        'serial_no': cells[0].get_text(strip=True),
                        'diary_case_no': self._extract_case_with_status(cells[1]),
                        'parties': self._clean_text(cells[2]),
                        'listing_info': self._extract_listing_details(cells[3])
                    }
                    cases.append(case_data)
            
            return {'cases': cases, 'table_type': 'case_listing'}
            
        except Exception as e:
            self.logger.error(f"Error parsing case table: {str(e)}")
            return {'error': f'Failed to parse case table: {str(e)}'}
    
    def _parse_generic_case_table(self, table):
        """Parse any table that looks like it contains case data"""
        try:
            cases = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    case_data = {
                        'row_data': [self._clean_text(cell) for cell in cells]
                    }
                    cases.append(case_data)
            
            return {'cases': cases, 'table_type': 'generic'}
            
        except Exception as e:
            self.logger.error(f"Error parsing generic table: {str(e)}")
            return {'error': f'Failed to parse generic table: {str(e)}'}
    
    def _is_case_results_table(self, table):
        """Check if table contains case results"""
        text = table.get_text().lower()
        case_indicators = ['case no', 'diary no', 'judgment', 'party', 'petitioner', 'respondent']
        return any(indicator in text for indicator in case_indicators)
    
    def _extract_case_number_with_dhc(self, cell):
        """Extract case number with DHC citation from judgment table"""
        try:
            text = self._clean_text(cell)
            
            # Extract case number and DHC citation
            case_data = {'text': text}
            
            # Look for DHC citation in blue font
            blue_font = cell.find('font', {'color': 'blue'})
            if blue_font:
                case_data['dhc_citation'] = blue_font.get_text(strip=True)
            
            # Extract main case number (before any font tags)
            main_text = cell.get_text(separator=' ', strip=True)
            lines = main_text.split()
            if lines:
                case_data['case_number'] = lines[0]
            
            return case_data
            
        except Exception as e:
            return {'text': self._clean_text(cell), 'error': str(e)}
    
    def _extract_case_with_status(self, cell):
        """Extract case number with status from case table"""
        try:
            text = self._clean_text(cell)
            case_data = {'text': text}
            
            # Extract status from colored font (red for DISPOSED, etc.)
            status_font = cell.find('font', {'color': 'red'})
            if status_font:
                case_data['status'] = status_font.get_text(strip=True).replace('[', '').replace(']', '')
            
            # Extract case type and number
            case_link = cell.find('a')
            if case_link:
                case_data['case_type'] = case_link.get_text(strip=True)
            
            # Extract orders link
            orders_link = cell.find('a', string='Orders')
            if not orders_link:
                orders_link = cell.find('a', href=lambda x: x and 'case-type-status-details' in x)
            
            if orders_link:
                case_data['orders_link'] = urljoin(self.base_url, orders_link.get('href', ''))
            
            return case_data
            
        except Exception as e:
            return {'text': self._clean_text(cell), 'error': str(e)}
    
    def _extract_listing_details(self, cell):
        """Extract listing date and court number details"""
        try:
            text = self._clean_text(cell)
            listing_data = {'text': text}
            
            # Use regex to extract structured data
            import re
            
            # Extract NEXT DATE
            next_date_match = re.search(r'NEXT DATE:\s*([^<\n\r]+?)(?=\s*(?:Last Date:|COURT NO:|$))', text)
            if next_date_match:
                listing_data['next_date'] = next_date_match.group(1).strip()
            
            # Extract Last Date
            last_date_match = re.search(r'Last Date:\s*([^<\n\r]+?)(?=\s*(?:COURT NO:|$))', text)
            if last_date_match:
                listing_data['last_date'] = last_date_match.group(1).strip()
            
            # Extract COURT NO
            court_no_match = re.search(r'COURT NO:\s*(\d+)', text)
            if court_no_match:
                listing_data['court_no'] = court_no_match.group(1).strip()
            
            return listing_data
            
        except Exception as e:
            return {'text': self._clean_text(cell), 'error': str(e)}
    
    def _extract_judgment_links(self, cell):
        """Extract judgment date and PDF/TXT links"""
        try:
            links = cell.find_all('a')
            judgment_data = {
                'text': self._clean_text(cell),
                'links': []
            }
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if href:
                    judgment_data['links'].append({
                        'url': urljoin(self.base_url, href),
                        'text': text,
                        'type': 'pdf' if 'pdf' in href.lower() else 'txt' if 'txt' in href.lower() else 'other'
                    })
            
            return judgment_data
            
        except Exception as e:
            return {'text': self._clean_text(cell), 'error': str(e)}
    
    def _parse_judgment_table_standardized(self, table):
        """Parse judgment table and return standardized format"""
        try:
            cases = []
            tbody = table.find('tbody')
            if not tbody:
                return {'error': 'No tbody found in judgment table'}
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # Extract case number and year from case no cell
                    case_info = self._extract_case_info(cells[1])
                    
                    # Extract petitioner and respondent from parties cell
                    parties = self._extract_parties(cells[3])
                    
                    # Extract judgment date and PDF link
                    judgment_info = self._extract_judgment_info(cells[2])
                    
                    case_data = {
                        'case_type': case_info.get('case_type', 'NA'),
                        'case_number': case_info.get('case_number', 'NA'),
                        'year': case_info.get('year', 'NA'),
                        'petitioner': parties.get('petitioner', 'NA'),
                        'respondent': parties.get('respondent', 'NA'),
                        'next_date': 'NA',  # Not available in judgment table
                        'last_date': 'NA',  # Not available in judgment table
                        'date_of_judgment_order': judgment_info.get('date', 'NA'),
                        'pdf_link': judgment_info.get('pdf_link', 'NA')
                    }
                    cases.append(case_data)
            
            return {'cases': cases}
            
        except Exception as e:
            self.logger.error(f"Error parsing judgment table: {str(e)}")
            return {'error': f'Failed to parse judgment table: {str(e)}'}
    
    def _parse_case_table_standardized(self, table):
        """Parse case table and return standardized format"""
        try:
            cases = []
            tbody = table.find('tbody')
            if not tbody:
                return {'error': 'No tbody found in case table'}
            
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # Extract case number and year from diary/case no cell
                    case_info = self._extract_case_info(cells[1])
                    
                    # Extract petitioner and respondent from parties cell
                    parties = self._extract_parties(cells[2])
                    
                    # Extract listing dates from listing cell
                    listing_info = self._extract_listing_dates(cells[3])
                    
                    case_data = {
                        'case_type': case_info.get('case_type', 'NA'),
                        'case_number': case_info.get('case_number', 'NA'),
                        'year': case_info.get('year', 'NA'),
                        'petitioner': parties.get('petitioner', 'NA'),
                        'respondent': parties.get('respondent', 'NA'),
                        'next_date': listing_info.get('next_date', 'NA'),
                        'last_date': listing_info.get('last_date', 'NA'),
                        'date_of_judgment_order': 'NA',  # Not available in case table
                        'pdf_link': 'NA'  # Not available in case table
                    }
                    cases.append(case_data)
            
            return {'cases': cases}
            
        except Exception as e:
            self.logger.error(f"Error parsing case table: {str(e)}")
            return {'error': f'Failed to parse case table: {str(e)}'}
    
    def _parse_generic_case_table_standardized(self, table):
        """Parse any table and return standardized format"""
        try:
            cases = []
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # Try to extract what we can from generic table
                    case_data = {
                        'case_type': 'NA',
                        'case_number': 'NA',
                        'year': 'NA',
                        'petitioner': 'NA',
                        'respondent': 'NA',
                        'next_date': 'NA',
                        'last_date': 'NA',
                        'date_of_judgment_order': 'NA',
                        'pdf_link': 'NA'
                    }
                    
                    # Try to find case info in first few cells
                    for i, cell in enumerate(cells[:3]):
                        text = self._clean_text(cell)
                        # Simple pattern to detect case numbers: anything-number/year
                        if re.search(r'.+-\d+/\d{4}', text):
                            case_info = self._extract_case_info(cell)
                            case_data.update({
                                'case_type': case_info.get('case_type', 'NA'),
                                'case_number': case_info.get('case_number', 'NA'),
                                'year': case_info.get('year', 'NA')
                            })
                            break
                    
                    cases.append(case_data)
            
            return {'cases': cases}
            
        except Exception as e:
            self.logger.error(f"Error parsing generic table: {str(e)}")
            return {'error': f'Failed to parse generic table: {str(e)}'}
    
    def _extract_case_info(self, cell):
        """Extract case type, number, and year from cell"""
        try:
            text = self._clean_text(cell)
            
            # Simple and reliable pattern that works for all formats:
            # W.P.(C)-11180/2025, CRL.M.C.-558/2025, O.M.P. (E) (COMM.)-123/2024, etc.
            # Just look for: (anything)-number/year
            pattern = r'(.+?)-(\d+)/(\d{4})'
            match = re.search(pattern, text)
            
            if match:
                case_type = match.group(1).strip()
                case_number = match.group(2).strip()
                year = match.group(3).strip()
                
                # Clean up case type - remove trailing dots and normalize spaces
                case_type = re.sub(r'\s+', ' ', case_type)  # Normalize spaces
                case_type = re.sub(r'\.+$', '', case_type)  # Remove trailing dots
                
                return {
                    'case_type': case_type,
                    'case_number': case_number,
                    'year': year
                }
            
            # Fallback: try to find number/year pattern and extract case type before it
            number_match = re.search(r'(\d+)/(\d{4})', text)
            if number_match:
                # Find where the number starts
                number_start = text.find(number_match.group(0))
                case_type_part = text[:number_start].strip()
                
                # Remove trailing dash or spaces
                case_type_part = re.sub(r'[-\s]+$', '', case_type_part).strip()
                
                if case_type_part:
                    return {
                        'case_type': case_type_part,
                        'case_number': number_match.group(1),
                        'year': number_match.group(2)
                    }
            
            return {'case_type': 'NA', 'case_number': 'NA', 'year': 'NA'}
            
        except Exception as e:
            return {'case_type': 'NA', 'case_number': 'NA', 'year': 'NA'}
    
    def _extract_parties(self, cell):
        """Extract petitioner and respondent names"""
        try:
            text = self._clean_text(cell)
            
            # Look for VS/Vs pattern
            vs_patterns = [r'\bVS\.?\s*', r'\bVs\.?\s*', r'\bvs\.?\s*']
            
            for pattern in vs_patterns:
                if re.search(pattern, text):
                    parts = re.split(pattern, text, 1)
                    if len(parts) == 2:
                        petitioner = parts[0].strip()
                        respondent = parts[1].strip()
                        
                        # Clean up common suffixes/prefixes
                        petitioner = re.sub(r'^(PETITIONER\s*:?\s*)', '', petitioner, flags=re.IGNORECASE).strip()
                        respondent = re.sub(r'^(RESPONDENT\s*:?\s*)', '', respondent, flags=re.IGNORECASE).strip()
                        
                        # Remove leading dots from respondent
                        respondent = re.sub(r'^\.+\s*', '', respondent).strip()
                        
                        return {
                            'petitioner': petitioner if petitioner else 'NA',
                            'respondent': respondent if respondent else 'NA'
                        }
            
            # If no VS found, return the whole text as petitioner
            return {'petitioner': text if text else 'NA', 'respondent': 'NA'}
            
        except Exception as e:
            return {'petitioner': 'NA', 'respondent': 'NA'}
    
    def _extract_listing_dates(self, cell):
        """Extract next date and last date from listing cell"""
        try:
            text = self._clean_text(cell)
            
            # Extract NEXT DATE
            next_date_match = re.search(r'NEXT DATE:\s*([^\r\n<]+?)(?=\s*(?:Last Date:|COURT NO:|$))', text)
            next_date = next_date_match.group(1).strip() if next_date_match else 'NA'
            
            # Extract Last Date
            last_date_match = re.search(r'Last Date:\s*([^\r\n<]+?)(?=\s*(?:COURT NO:|$))', text)
            last_date = last_date_match.group(1).strip() if last_date_match else 'NA'
            
            return {
                'next_date': next_date,
                'last_date': last_date
            }
            
        except Exception as e:
            return {'next_date': 'NA', 'last_date': 'NA'}
    
    def _extract_judgment_info(self, cell):
        """Extract judgment date and PDF link"""
        try:
            links = cell.find_all('a')
            pdf_link = 'NA'
            date = 'NA'
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if 'pdf' in href.lower():
                    pdf_link = urljoin(self.base_url, href)
                    # Extract date from link text (e.g., "02-07-2025 (pdf)")
                    date_match = re.search(r'(\d{2}-\d{2}-\d{4})', text)
                    if date_match:
                        date = date_match.group(1)
                    break
            
            return {
                'date': date,
                'pdf_link': pdf_link
            }
            
        except Exception as e:
            return {'date': 'NA', 'pdf_link': 'NA'}
    
    def _clean_text(self, element):
        """Clean text from HTML element"""
        if hasattr(element, 'get_text'):
            text = element.get_text(separator=' ', strip=True)
        else:
            text = str(element).strip()
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scraper = DelhiCourtScraper()
    
    # Test case from the prompt
    result = scraper.search_case('CRLMM', '558', '2025')
    print(json.dumps(result, indent=2, default=str))
