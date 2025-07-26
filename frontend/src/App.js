import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Barcode Scanner Component
const BarcodeScanner = ({ onScan, isScanning, onToggle }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [hasCamera, setHasCamera] = useState(false);
  
  useEffect(() => {
    if (isScanning) {
      startCamera();
    } else {
      stopCamera();
    }
    
    return () => stopCamera();
  }, [isScanning]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setHasCamera(true);
        
        // Start scanning for barcodes
        setTimeout(() => scanForBarcode(), 1000);
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setHasCamera(false);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setHasCamera(false);
  };

  const scanForBarcode = async () => {
    if (!isScanning || !videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Try to detect barcode using BarcodeDetector if available
      if ('BarcodeDetector' in window) {
        try {
          const detector = new window.BarcodeDetector();
          const barcodes = await detector.detect(canvas);
          
          if (barcodes.length > 0) {
            onScan(barcodes[0].rawValue);
            return;
          }
        } catch (err) {
          console.error('BarcodeDetector error:', err);
        }
      }
    }

    // Continue scanning
    if (isScanning) {
      setTimeout(() => scanForBarcode(), 100);
    }
  };

  return (
    <div className="barcode-scanner">
      <div className="camera-container relative">
        <video 
          ref={videoRef} 
          className="w-full max-w-md rounded-lg shadow-lg"
          style={{ display: isScanning ? 'block' : 'none' }}
        />
        <canvas 
          ref={canvasRef} 
          style={{ display: 'none' }}
        />
        
        {isScanning && (
          <div className="scanner-overlay">
            <div className="scanner-line"></div>
            <p className="text-white text-sm mt-4 text-center">
              Position barcode in the center of the screen
            </p>
          </div>
        )}
      </div>
      
      <button
        onClick={onToggle}
        className={`mt-4 px-6 py-3 rounded-lg font-semibold transition-colors ${
          isScanning 
            ? 'bg-red-500 hover:bg-red-600 text-white' 
            : 'bg-blue-500 hover:bg-blue-600 text-white'
        }`}
      >
        {isScanning ? '📹 Stop Scanning' : '📱 Start Scanning'}
      </button>
      
      {!hasCamera && isScanning && (
        <p className="text-red-500 text-sm mt-2">
          Camera access required. Please allow camera permissions.
        </p>
      )}
    </div>
  );
};

// Manual Barcode Input Component
const ManualInput = ({ onSubmit, loading }) => {
  const [barcode, setBarcode] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (barcode.trim()) {
      onSubmit(barcode.trim());
      setBarcode('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="manual-input">
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          placeholder="Enter barcode manually (e.g., 3017620422003)"
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !barcode.trim()}
          className="px-6 py-3 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white rounded-lg font-semibold transition-colors"
        >
          {loading ? '🔍 Analyzing...' : '🔍 Analyze'}
        </button>
      </div>
    </form>
  );
};

// Analysis Results Component
const AnalysisResults = ({ analysis }) => {
  if (!analysis) return null;

  const getScoreColor = (score) => {
    if (score >= 4) return 'text-green-500';
    if (score >= 3) return 'text-yellow-500';
    if (score >= 2) return 'text-orange-500';
    return 'text-red-500';
  };

  const getScoreStars = (score) => {
    return '⭐'.repeat(Math.round(score));
  };

  const getProcessingColor = (level) => {
    switch (level) {
      case 'Unprocessed': return 'bg-green-100 text-green-800';
      case 'Minimally processed': return 'bg-blue-100 text-blue-800';
      case 'Processed': return 'bg-yellow-100 text-yellow-800';
      case 'Ultra-processed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="analysis-results bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto">
      {/* Product Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">{analysis.product_name}</h2>
        {analysis.brand && (
          <p className="text-gray-600 mt-1">{analysis.brand}</p>
        )}
        <p className="text-sm text-gray-500">Barcode: {analysis.barcode}</p>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="score-card bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">Overall Health Score</h3>
          <div className={`text-2xl font-bold ${getScoreColor(analysis.nutrition_score)}`}>
            {getScoreStars(analysis.nutrition_score)} {analysis.nutrition_score.toFixed(1)}/5
          </div>
        </div>

        <div className="score-card bg-gradient-to-r from-purple-50 to-purple-100 p-4 rounded-lg">
          <h3 className="font-semibold text-purple-800 mb-2">Diabetic Friendly</h3>
          <div className={`text-2xl font-bold ${getScoreColor(analysis.diabetic_score)}`}>
            {getScoreStars(analysis.diabetic_score)} {analysis.diabetic_score.toFixed(1)}/5
          </div>
        </div>
      </div>

      {/* Processing Level */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-3">Processing Level (NOVA Classification)</h3>
        <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getProcessingColor(analysis.processing_level)}`}>
          {analysis.processing_level}
        </span>
        {analysis.analysis_details.processing_analysis.classification_reason && (
          <p className="text-sm text-gray-600 mt-2">
            {analysis.analysis_details.processing_analysis.classification_reason}
          </p>
        )}
      </div>

      {/* WHO Guidelines Compliance */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-3">WHO Guidelines Compliance</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {Object.entries(analysis.who_compliance).map(([key, compliant]) => (
            <div key={key} className={`p-3 rounded-lg ${compliant ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} border`}>
              <div className="flex items-center">
                <span className={`text-lg ${compliant ? 'text-green-500' : 'text-red-500'}`}>
                  {compliant ? '✅' : '❌'}
                </span>
                <span className="ml-2 text-sm font-medium capitalize">
                  {key.replace('_', ' ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Nutritional Information */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-3">Nutritional Information (per 100g)</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 text-sm">
          {Object.entries(analysis.nutritional_info)
            .filter(([_, value]) => value !== null && value !== undefined)
            .map(([key, value]) => (
            <div key={key} className="bg-gray-50 p-2 rounded">
              <div className="font-medium text-gray-600 capitalize">
                {key.replace('_', ' ')}
              </div>
              <div className="text-gray-800 font-semibold">
                {typeof value === 'number' ? value.toFixed(1) + 'g' : value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Analysis Details */}
      <details className="cursor-pointer">
        <summary className="font-semibold text-gray-800 hover:text-blue-600 transition-colors">
          📊 Detailed Analysis
        </summary>
        <div className="mt-3 space-y-3 text-sm">
          {Object.entries(analysis.analysis_details).map(([category, details]) => (
            <div key={category} className="bg-gray-50 p-3 rounded">
              <h4 className="font-medium text-gray-700 mb-2 capitalize">
                {category.replace('_', ' ')}
              </h4>
              <div className="space-y-1">
                {Object.entries(details).map(([key, value]) => (
                  <div key={key} className="text-gray-600">
                    <strong>{key.replace('_', ' ')}:</strong> {value}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
};

// Scan History Component
const ScanHistory = ({ history, onSelectProduct }) => {
  if (!history || history.length === 0) return null;

  return (
    <div className="scan-history bg-white rounded-lg shadow-lg p-6 max-w-2xl mx-auto mt-6">
      <h3 className="font-semibold text-gray-800 mb-4">📜 Recent Scans</h3>
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {history.slice(0, 10).map((item) => (
          <div
            key={item.id}
            onClick={() => onSelectProduct(item.barcode)}
            className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors"
          >
            <div className="flex-1">
              <p className="font-medium text-gray-800 truncate">{item.product_name}</p>
              <p className="text-sm text-gray-600">{item.processing_level}</p>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <span className="text-sm">⭐{item.nutrition_score.toFixed(1)}</span>
              <span className="text-sm">💊{item.diabetic_score.toFixed(1)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [isScanning, setIsScanning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [scanHistory, setScanHistory] = useState([]);

  useEffect(() => {
    loadScanHistory();
  }, []);

  const loadScanHistory = async () => {
    try {
      const response = await axios.get(`${API}/scan-history`);
      setScanHistory(response.data);
    } catch (err) {
      console.error('Failed to load scan history:', err);
    }
  };

  const analyzeProduct = async (barcode) => {
    setLoading(true);
    setError('');
    setIsScanning(false);
    
    try {
      const response = await axios.post(`${API}/analyze-product`, { barcode });
      setAnalysis(response.data);
      loadScanHistory(); // Refresh history
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        'Failed to analyze product. Please check the barcode and try again.'
      );
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = (barcode) => {
    analyzeProduct(barcode);
  };

  const toggleScanning = () => {
    setIsScanning(!isScanning);
    setError('');
  };

  const handleHistorySelect = async (barcode) => {
    try {
      const response = await axios.get(`${API}/product/${barcode}`);
      setAnalysis(response.data);
    } catch (err) {
      // If not cached, analyze again
      analyzeProduct(barcode);
    }
  };

  return (
    <div className="App min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            🥗 Food Health Analyzer
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Scan any food product barcode to get instant analysis: diabetic friendliness, 
            processing level, WHO compliance, and overall health score.
          </p>
        </div>

        {/* Scanner Section */}
        <div className="text-center mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Scan Product</h2>
            
            <BarcodeScanner
              onScan={handleScan}
              isScanning={isScanning}
              onToggle={toggleScanning}
            />
          </div>

          {/* Manual Input */}
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg mx-auto">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Or Enter Barcode Manually</h3>
            <ManualInput onSubmit={analyzeProduct} loading={loading} />
            <p className="text-xs text-gray-500 mt-2">
              Try: 3017620422003 (Nutella), 3274080005003 (Perrier), or 8712566451111
            </p>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center mb-8">
            <div className="inline-flex items-center px-6 py-3 bg-blue-100 text-blue-800 rounded-lg">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-800" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing product...
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center mb-8">
            <div className="inline-block px-6 py-3 bg-red-100 text-red-800 rounded-lg max-w-md">
              ❌ {error}
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysis && <AnalysisResults analysis={analysis} />}

        {/* Scan History */}
        <ScanHistory 
          history={scanHistory} 
          onSelectProduct={handleHistorySelect}
        />

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500 text-sm">
          <p>Data powered by Open Food Facts | Analysis based on WHO guidelines</p>
        </div>
      </div>
    </div>
  );
};

export default App;