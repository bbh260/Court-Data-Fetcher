#!/usr/bin/env python3
"""
Minimal Flask Frontend for Delhi High Court Case Scraper
Single-page application with form, results display, and database logging.
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import requests
from delhi_court_scraper import DelhiCourtScraper

app = Flask(__name__)
app.secret_key = 'delhi_court_scraper_secret_key_2025'  # Change this in production

# Configuration
DATABASE_PATH = 'case_searches.db'
UPLOAD_FOLDER = 'downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure download folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handle all database operations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create searches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS searches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        case_type TEXT NOT NULL,
                        case_number TEXT NOT NULL,
                        year TEXT NOT NULL,
                        search_duration REAL,
                        status TEXT NOT NULL,
                        raw_response TEXT,
                        parsed_result TEXT,
                        error_message TEXT,
                        user_ip TEXT
                    )
                ''')
                
                # Create index for faster searches
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_case_search 
                    ON searches(case_type, case_number, year)
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def log_search(self, case_type, case_number, year, duration, status, 
                   raw_response, parsed_result, error_message, user_ip):
        """Log a search query to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO searches 
                    (case_type, case_number, year, search_duration, status, 
                     raw_response, parsed_result, error_message, user_ip)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    case_type, case_number, year, duration, status,
                    json.dumps(raw_response) if raw_response else None,
                    json.dumps(parsed_result) if parsed_result else None,
                    error_message, user_ip
                ))
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to log search: {e}")
            return None
    
    def get_recent_searches(self, limit=10):
        """Get recent searches for display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT case_type, case_number, year, timestamp, status
                    FROM searches 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                return [
                    {
                        'case_type': row[0],
                        'case_number': row[1], 
                        'year': row[2],
                        'timestamp': row[3],
                        'status': row[4]
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Failed to get recent searches: {e}")
            return []
    
    def clear_all_searches(self):
        """Clear all search history from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM searches')
                conn.commit()
                deleted_count = cursor.rowcount
                logger.info(f"Cleared {deleted_count} search records from database")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to clear search history: {e}")
            return 0

# Initialize database
db_manager = DatabaseManager(DATABASE_PATH)
scraper = DelhiCourtScraper()

# Case types mapping: display_name -> website_code
CASE_TYPES_MAPPING = {
    'ARB.A.': 'AAP',
    'ARB. A. (COMM.)': 'ARBACOMM',
    'ARB.P.': 'AA',
    'BAIL APPLN.': 'BA',
    'CA': 'CAA',
    'CA (COMM.IPD-CR)': 'CACR',
    'C.A.(COMM.IPD-GI)': 'CAG',
    'C.A.(COMM.IPD-PAT)': 'CAP',
    'C.A.(COMM.IPD-PV)': 'CAPP',
    'C.A.(COMM.IPD-TM)': 'CAT',
    'CAVEAT(CO.)': 'CAVC',
    'CC(ARB.)': 'CC',
    'CCP(CO.)': 'CCPCO',
    'CCP(REF)': 'CCPRF',
    'CEAC': 'CEAC',
    'CEAR': 'CEAR',
    'CHAT.A.C.': 'CHATAC',
    'CHAT.A.REF': 'CHATRF',
    'CMI': 'CMI',
    'CM(M)': 'CMM',
    'CM(M)-IPD': 'CMMI',
    'C.O.': 'CO',
    'CO.APP.': 'COA',
    'CO.APPL.(C)': 'CAC',
    'CO.APPL.(M)': 'CAM',
    'CO.A(SB)': 'COASB',
    'C.O.(COMM.IPD-CR)': 'COC',
    'C.O.(COMM.IPD-GI)': 'COG',
    'C.O.(COMM.IPD-PAT)': 'COP',
    'C.O. (COMM.IPD-TM)': 'COT',
    'CO.EX.': 'COEX',
    'CONT.APP.(C)': 'CCA',
    'CONT.CAS(C)': 'CCP',
    'CONT.CAS.(CRL)': 'CRLCC',
    'CO.PET.': 'CP',
    'C.REF.(O)': 'CRULE',
    'CRL.A.': 'CRLA',
    'CRL.L.P.': 'CRLMP',
    'CRL.M.C.': 'CRLMM',
    'CRL.M.(CO.)': 'CRLMC',
    'CRL.M.I.': 'CRLMI',
    'CRL.O.': 'CRLO',
    'CRL.O.(CO.)': 'CRLOC',
    'CRL.REF.': 'CRLRF',
    'CRL.REV.P.': 'CRLR',
    'CRL.REV.P.(MAT.)': 'CRLRMAT',
    'CRL.REV.P.(NDPS)': 'CRLRNDPS',
    'CRL.REV.P.(NI)': 'CRLRNI',
    'C.R.P.': 'CR',
    'CRP-IPD': 'CRI',
    'C.RULE': 'CRULE',
    'CS(COMM)': 'SC',
    'CS(OS)': 'S',
    'CS(OS) GP': 'S',
    'CUSAA': 'CUSAA',
    'CUS.A.C.': 'CUSAC',
    'CUS.A.R.': 'CUSAR',
    'CUSTOM A.': 'CUSTOMA',
    'DEATH SENTENCE REF.': 'DSRF',
    'EDC': 'EDC',
    'EDR': 'EDR',
    'EFA(COMM)': 'EFAC',
    'EFA(OS)': 'EFAOS',
    'EFA(OS)  (COMM)': 'EFAOSCOMM',
    'EFA(OS)(IPD)': 'EFI',
    'EL.PET.': 'EP',
    'ETR': 'ETR',
    'EX.F.A.': 'EFA',
    'EX.P.': 'EX',
    'EX.S.A.': 'ESA',
    'FAO': 'FAO',
    'FAO (COMM)': 'FAOC',
    'FAO-IPD': 'FAI',
    'FAO(OS)': 'FAOOS',
    'FAO(OS) (COMM)': 'FAC',
    'FAO(OS)(IPD)': 'FAOI',
    'GCAC': 'GCAC',
    'GCAR': 'GCAR',
    'GTA': 'GTA',
    'GTC': 'GTC',
    'GTR': 'GTR',
    'I.A.': 'IA',
    'I.P.A.': 'IPA',
    'ITA': 'ITA',
    'ITC': 'ITC',
    'ITR': 'ITR',
    'ITSA': 'ITSA',
    'LA.APP.': 'LAA',
    'LPA': 'LPA',
    'MAC.APP.': 'MACA',
    'MAT.': 'MAT',
    'MAT.APP.': 'MATA',
    'MAT.APP.(F.C.)': 'MATFC',
    'MAT.CASE': 'MATC',
    'MAT.REF.': 'MATRF',
    'MISC. APPEAL(PMLA)': 'PMLA',
    'OA': 'OA',
    'OCJA': 'OCJA',
    'O.M.P.': 'OMP',
    'O.M.P. (COMM)': 'OMPCOMM',
    'OMP (CONT.)': 'OMP(CONT.)',
    'O.M.P. (E)': 'OE',
    'O.M.P. (E) (COMM.)': 'OMPECOMM',
    'O.M.P.(EFA)(COMM.)': 'OMPEFACOMM',
    'OMP (ENF.) (COMM.)': 'OMPENFCOMM',
    'O.M.P.(I)': 'OI',
    'O.M.P.(I) (COMM.)': 'OMPICOMM',
    'O.M.P. (J) (COMM.)': 'OMPICOMM',
    'O.M.P. (MISC.)': 'OMPMISC',
    'O.M.P.(MISC.)(COMM.)': 'OMPMISCCOMM',
    'O.M.P.(T)': 'OMPT',
    'O.M.P. (T) (COMM.)': 'OMPTCOMM',
    'O.REF.': 'OREF',
    'RC.REV.': 'RCR',
    'RC.S.A.': 'RCSA',
    'RERA APPEAL': 'RERA',
    'REVIEW PET.': 'REVIEWPET',
    'RFA': 'RFA',
    'RFA(COMM)': 'RFAC',
    'RFA-IPD': 'RFI',
    'RFA(OS)': 'RFAOS',
    'RFA(OS)(COMM)': 'RFC',
    'RF(OS)(IPD)': 'RFO',
    'RSA': 'RSA',
    'SCA': 'SCA',
    'SDR': 'SDR',
    'SERTA': 'SERTA',
    'ST.APPL.': 'STA',
    'STC': 'STC',
    'ST.REF.': 'STR',
    'SUR.T.REF.': 'SRTRF',
    'TEST.CAS.': 'PR',
    'TR.P.(C)': 'TRPC',
    'TR.P.(C.)': 'TPC',
    'TR.P.(CRL.)': 'TRP',
    'VAT APPEAL': 'VATA',
    'W.P.(C)': 'CW',
    'W.P.(C)-IPD': 'WO',
    'WP(C)(IPD)': 'WC',
    'W.P.(CRL)': 'CRLW',
    'WTA': 'WTA',
    'WTC': 'WTC',
    'WTR': 'WTR'
}

# Get list of case types for dropdown (display names)
CASE_TYPES = list(CASE_TYPES_MAPPING.keys())

@app.route('/')
def index():
    """Main page with search form and recent searches"""
    recent_searches = db_manager.get_recent_searches(5)
    return render_template('index.html', 
                         case_types=CASE_TYPES, 
                         recent_searches=recent_searches)

@app.route('/search', methods=['POST'])
def search_case():
    """Handle case search requests"""
    start_time = datetime.now()
    user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    try:
        # Get form data
        case_type_display = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        year = request.form.get('year', '').strip()
        
        # Validate input
        if not all([case_type_display, case_number, year]):
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
        if not case_number.isdigit():
            flash('Case number must be numeric!', 'error')
            return redirect(url_for('index'))
        
        if not year.isdigit() or len(year) != 4:
            flash('Year must be a 4-digit number!', 'error')
            return redirect(url_for('index'))
        
        # Convert display case type to website code
        case_type_code = CASE_TYPES_MAPPING.get(case_type_display)
        if not case_type_code:
            flash(f'Invalid case type: {case_type_display}', 'error')
            return redirect(url_for('index'))
        
        logger.info(f"Searching for case: {case_type_display} ({case_type_code})-{case_number}/{year}")
        
        # Perform search using the website code
        result = scraper.search_case(case_type_code, case_number, year)
        
        # Calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Determine status
        if 'error' in result:
            status = 'ERROR'
            error_message = result['error']
            parsed_result = None
        elif 'data' in result and 'cases' in result['data'] and result['data']['cases']:
            status = 'SUCCESS'
            error_message = None
            parsed_result = result
        else:
            status = 'NO_RESULTS'
            error_message = 'No cases found'
            parsed_result = result
        
        # Log to database
        db_manager.log_search(
            case_type_display, case_number, year, duration, status,
            result, parsed_result, error_message, user_ip
        )
        
        # Handle results
        if status == 'ERROR':
            flash(f'Search failed: {error_message}', 'error')
            return redirect(url_for('index'))
        elif status == 'NO_RESULTS':
            flash('No cases found for the given criteria.', 'warning')
            return redirect(url_for('index'))
        else:
            flash(f'Search completed successfully in {duration:.2f} seconds!', 'success')
            # Store results in session for the results page
            session['search_result'] = parsed_result
            session['search_duration'] = duration
            session['search_query'] = {
                'case_type': case_type_display,
                'case_number': case_number,
                'year': year
            }
            return redirect(url_for('search_results'))
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/results')
def search_results():
    """Display search results in a separate page"""
    search_result = session.get('search_result')
    search_duration = session.get('search_duration')
    search_query = session.get('search_query')
    
    if not search_result:
        flash('No search results found. Please perform a search first.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html',
                         search_result=search_result,
                         search_duration=search_duration,
                         search_query=search_query)

@app.route('/download_pdf')
def download_pdf():
    """Download PDF from the court website"""
    pdf_url = request.args.get('url')
    case_id = request.args.get('case_id', 'document')
    
    if not pdf_url:
        flash('No PDF URL provided!', 'error')
        return redirect(url_for('index'))
    
    try:
        logger.info(f"Downloading PDF: {pdf_url}")
        
        # Download the PDF
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Generate filename
        filename = f"{secure_filename(case_id)}.pdf"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"PDF saved: {filepath}")
        
        # Send file to user
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except requests.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        flash('Failed to download PDF. The link may be broken.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Unexpected error downloading PDF: {e}")
        flash('An error occurred while downloading the PDF.', 'error')
        return redirect(url_for('index'))

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for programmatic access"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        case_type = data.get('case_type', '').strip().upper()
        case_number = data.get('case_number', '').strip()
        year = data.get('year', '').strip()
        
        if not all([case_type, case_number, year]):
            return jsonify({'error': 'case_type, case_number, and year are required'}), 400
        
        result = scraper.search_case(case_type, case_number, year)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear_history', methods=['POST'])
def clear_search_history():
    """Clear all search history"""
    try:
        deleted_count = db_manager.clear_all_searches()
        if deleted_count > 0:
            flash(f'Successfully cleared {deleted_count} search records from history!', 'success')
        else:
            flash('No search history found to clear.', 'warning')
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Failed to clear search history: {e}")
        flash('An error occurred while clearing search history.', 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(DATABASE_PATH) else 'disconnected'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('index.html', 
                         case_types=CASE_TYPES,
                         recent_searches=db_manager.get_recent_searches(5)), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('index.html', 
                         case_types=CASE_TYPES,
                         recent_searches=db_manager.get_recent_searches(5)), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
