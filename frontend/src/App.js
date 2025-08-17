import React, { useState, useRef, useCallback, useEffect } from 'react';
import axios from 'axios';
import { Camera, Heart, Brain, Activity, Target, TrendingUp, AlertCircle, CheckCircle, Eye, Fingerprint, RefreshCw } from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [scanMode, setScanMode] = useState('face'); // 'face' or 'finger'
  const [isScanning, setIsScanning] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [healthHistory, setHealthHistory] = useState([]);
  const [ws, setWs] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [scanProgress, setScanProgress] = useState(0);
  const [analysisPhase, setAnalysisPhase] = useState('');
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Fetch health history
  const fetchHealthHistory = useCallback(async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/health/history`);
      if (response.data.success) {
        setHealthHistory(response.data.readings);
      }
    } catch (error) {
      console.error('Error fetching health history:', error);
    }
  }, []);

  useEffect(() => {
    fetchHealthHistory();
  }, [fetchHealthHistory]);

  // Start camera
  const startCamera = useCallback(async () => {
    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
    } catch (error) {
      setCameraError('Camera access denied. Please allow camera permissions.');
      console.error('Camera error:', error);
    }
  }, []);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  // Simulate scanning progress
  const simulateScanProgress = useCallback(() => {
    const phases = [
      { phase: 'Detecting face...', progress: 20 },
      { phase: 'Analyzing facial features...', progress: 40 },
      { phase: 'Processing emotions...', progress: 60 },
      { phase: 'Calculating health metrics...', progress: 80 },
      { phase: 'Generating recommendations...', progress: 100 }
    ];

    phases.forEach((phaseData, index) => {
      setTimeout(() => {
        setAnalysisPhase(phaseData.phase);
        setScanProgress(phaseData.progress);
      }, index * 800);
    });
  }, []);

  // Start scanning
  const startScanning = useCallback(async () => {
    if (!videoRef.current) return;

    setIsScanning(true);
    setScanResults(null);
    setScanProgress(0);
    setAnalysisPhase('Initializing scan...');
    
    try {
      await startCamera();
      
      // Start progress simulation
      simulateScanProgress();
      
      // Create WebSocket connection
      const websocket = new WebSocket(`${BACKEND_URL.replace('http', 'ws')}/api/ws/scan`);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
        setWs(websocket);
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'analysis_result' && data.results.length > 0) {
          setScanResults(data.results[0]);
          setIsScanning(false);
          setScanProgress(100);
          setAnalysisPhase('Scan complete!');
          fetchHealthHistory();
        }
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsScanning(false);
        setAnalysisPhase('Connection error');
      };
      
      // Capture and send frame after 4 seconds (when progress reaches 100%)
      setTimeout(() => {
        captureAndSendFrame(websocket);
      }, 4000);
      
    } catch (error) {
      console.error('Scanning error:', error);
      setIsScanning(false);
      setAnalysisPhase('Scan failed');
    }
  }, [startCamera, simulateScanProgress, fetchHealthHistory]);

  // Capture frame and send for analysis
  const captureAndSendFrame = useCallback((websocket) => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    
    context.drawImage(videoRef.current, 0, 0);
    
    const dataURL = canvas.toDataURL('image/jpeg', 0.8);
    
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        frame: dataURL,
        timestamp: Date.now(),
        scanMode: scanMode
      }));
    }
  }, [scanMode]);

  // Stop scanning
  const stopScanning = useCallback(() => {
    setIsScanning(false);
    setScanProgress(0);
    setAnalysisPhase('');
    stopCamera();
    
    if (ws) {
      ws.close();
      setWs(null);
    }
  }, [ws, stopCamera]);

  // Get health score color
  const getHealthScoreColor = (score) => {
    if (score < 0.3) return 'text-green-600';
    if (score < 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Get health score status
  const getHealthStatus = (results) => {
    if (!results) return { status: 'Unknown', color: 'gray' };
    
    const avgScore = (results.stress_level + results.anxiety_score + results.depression_score) / 3;
    
    if (avgScore < 0.3) return { status: 'Excellent', color: 'green' };
    if (avgScore < 0.6) return { status: 'Good', color: 'blue' };
    if (avgScore < 0.8) return { status: 'Moderate', color: 'yellow' };
    return { status: 'Attention Needed', color: 'red' };
  };

  const healthStatus = getHealthStatus(scanResults);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800">HealthScan</h1>
                <p className="text-sm text-slate-600">AI Health Monitoring</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                <Activity className="w-3 h-3 mr-1" />
                Live
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Scan Mode Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-blue-600" />
              <span>Select Scan Mode</span>
            </CardTitle>
            <CardDescription>Choose your preferred health scanning method</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <Button
                variant={scanMode === 'face' ? 'default' : 'outline'}
                className="h-20 flex flex-col items-center space-y-2"
                onClick={() => setScanMode('face')}
              >
                <Eye className="w-6 h-6" />
                <span>Face Scan</span>
                <span className="text-xs opacity-70">Stress, Anxiety, Mood</span>
              </Button>
              <Button
                variant={scanMode === 'finger' ? 'default' : 'outline'}
                className="h-20 flex flex-col items-center space-y-2"
                onClick={() => setScanMode('finger')}
                disabled={true}
              >
                <Fingerprint className="w-6 h-6" />
                <span>Finger Scan</span>
                <span className="text-xs opacity-70">Coming Soon</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scanning Interface */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Camera className="w-5 h-5 text-blue-600" />
                  <span>{scanMode === 'face' ? 'Face Scanner' : 'Finger Scanner'}</span>
                </CardTitle>
                <CardDescription>
                  {scanMode === 'face' 
                    ? 'Position your face in the camera frame for analysis' 
                    : 'Place your finger over the camera lens'}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Camera Preview */}
                <div className="relative">
                  <div className="w-full h-64 bg-slate-900 rounded-lg overflow-hidden relative">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                    <canvas ref={canvasRef} style={{ display: 'none' }} />
                    
                    {/* Scanning Overlay */}
                    {isScanning && (
                      <div className="absolute inset-0 bg-blue-600/10 flex items-center justify-center">
                        <div className="w-32 h-32 border-2 border-blue-500 rounded-lg animate-pulse">
                          <div className="w-full h-full border border-blue-300 rounded-lg animate-ping" />
                        </div>
                      </div>
                    )}
                    
                    {/* Face Detection Frame */}
                    {scanMode === 'face' && !isScanning && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-48 h-56 border-2 border-white/50 rounded-lg flex items-center justify-center">
                          <span className="text-white/70 text-sm">Position your face here</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Camera Error */}
                {cameraError && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-700">
                      {cameraError}
                    </AlertDescription>
                  </Alert>
                )}

                {/* Scan Progress */}
                {isScanning && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-600">{analysisPhase}</span>
                      <span className="text-slate-600">{scanProgress}%</span>
                    </div>
                    <Progress value={scanProgress} className="h-2" />
                  </div>
                )}

                {/* Scan Controls */}
                <div className="flex space-x-2">
                  {!isScanning ? (
                    <Button 
                      onClick={startScanning}
                      className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                      disabled={scanMode === 'finger'}
                    >
                      <Activity className="w-4 h-4 mr-2" />
                      Start {scanMode === 'face' ? 'Face' : 'Finger'} Scan
                    </Button>
                  ) : (
                    <Button 
                      onClick={stopScanning}
                      variant="outline"
                      className="flex-1"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Stop Scan
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          <div className="space-y-4">
            {scanResults ? (
              <>
                {/* Health Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="flex items-center space-x-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span>Health Status</span>
                      </span>
                      <Badge 
                        variant="outline"
                        className={`${
                          healthStatus.color === 'green' ? 'border-green-500 text-green-700' :
                          healthStatus.color === 'blue' ? 'border-blue-500 text-blue-700' :
                          healthStatus.color === 'yellow' ? 'border-yellow-500 text-yellow-700' :
                          'border-red-500 text-red-700'
                        }`}
                      >
                        {healthStatus.status}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Emotion */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Current Emotion</span>
                      <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                        {scanResults.emotion}
                      </Badge>
                    </div>

                    {/* Health Metrics */}
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>Stress Level</span>
                          <span className={getHealthScoreColor(scanResults.stress_level)}>
                            {Math.round(scanResults.stress_level * 100)}%
                          </span>
                        </div>
                        <Progress value={scanResults.stress_level * 100} className="h-2" />
                      </div>

                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>Anxiety Score</span>
                          <span className={getHealthScoreColor(scanResults.anxiety_score)}>
                            {Math.round(scanResults.anxiety_score * 100)}%
                          </span>
                        </div>
                        <Progress value={scanResults.anxiety_score * 100} className="h-2" />
                      </div>

                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>Depression Indicators</span>
                          <span className={getHealthScoreColor(scanResults.depression_score)}>
                            {Math.round(scanResults.depression_score * 100)}%
                          </span>
                        </div>
                        <Progress value={scanResults.depression_score * 100} className="h-2" />
                      </div>

                      <div className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>Glucose Simulation</span>
                          <span className="font-semibold text-purple-600">
                            {scanResults.glucose_simulation} mg/dL
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Recommendations */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Brain className="w-5 h-5 text-purple-600" />
                      <span>Recommendations</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {scanResults.recommendations?.map((rec, index) => (
                        <Alert key={index} className="border-blue-200 bg-blue-50">
                          <AlertDescription className="text-blue-700 text-sm">
                            {rec}
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center h-64 text-center">
                  <Activity className="w-12 h-12 text-slate-400 mb-4" />
                  <h3 className="text-lg font-semibold text-slate-600 mb-2">Ready to Scan</h3>
                  <p className="text-slate-500 text-sm">
                    Start a {scanMode} scan to see your health metrics
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Health History */}
        {healthHistory.length > 0 && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <span>Health History</span>
              </CardTitle>
              <CardDescription>Your recent health scan results</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {healthHistory.slice(0, 5).map((reading, index) => (
                  <div key={reading.id || index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Heart className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">
                          {new Date(reading.timestamp * 1000).toLocaleString()}
                        </p>
                        <p className="text-xs text-slate-600">
                          {reading.emotion} • Glucose: {reading.glucose_simulation} mg/dL
                        </p>
                      </div>
                    </div>
                    <div className="flex space-x-2 text-xs">
                      <Badge variant="outline" className="text-red-600 border-red-300">
                        Stress: {Math.round(reading.stress_level * 100)}%
                      </Badge>
                      <Badge variant="outline" className="text-yellow-600 border-yellow-300">
                        Anxiety: {Math.round(reading.anxiety_score * 100)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;