import React, { useState, useMemo, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Search, BookOpen, GraduationCap, Users, Star, ArrowRight, ChevronDown, ChevronUp, ArrowLeft, Settings, User, Bell, LogOut } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

// UW Undergraduate Programs (alphabetical)
const uwPrograms = [
  'Architectural Engineering', 
  'Architecture', 
  'Biomedical Engineering', 
  'Chemical Engineering', 
  'Civil Engineering', 
  'Computer Engineering', 
  'Electrical Engineering', 
  'Environmental Engineering', 
  'Geological Engineering', 
  'Management Engineering', 
  'Mechanical Engineering', 
  'Mechatronics Engineering', 
  'Software Engineering', 
  'Systems Design Engineering'
];

// Academic terms
const academicTerms = ['1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B'];

const minors = [
  "Computing Option",
  "Software Engineering Option",
  "Statistics Option",
  "Mechatronics Option",
  "Quantum Engineering Option",
  "Environmental Engineering Option",
  "Computer Engineering Option",
  "Physical Sciences Option",
  "Biomechanics Option",
  "Life Sciences Option",
  "Entrepreneurship Option",
  "Artificial Intelligence Option",
  "Management Science Option"
];

interface UserSelections {
  program: string;
  academicTerm: string;
  minor: string;
}

interface Course {
  code: string;
  title: string;
  description: string;
  // Optional fields for backward compatibility
  id?: string;
  name?: string;
  credits?: number;
  prerequisites?: string[];
  programs?: string[];
  terms?: string[];
  keywords?: string[];
}

interface CourseWithScore {
  course: Course;
  score: number;
}

const Index = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [selections, setSelections] = useState<UserSelections>({
    program: '',
    academicTerm: '',
    minor: ''
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [executedSearchQuery, setExecutedSearchQuery] = useState('');
  const [userChoice, setUserChoice] = useState<'show-all' | 'search' | ''>('');
  const [expandedCourse, setExpandedCourse] = useState<string | null>(null);
  const [programSearch, setProgramSearch] = useState('');
  const [showProfile, setShowProfile] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [eligibleCourseCodes, setEligibleCourseCodes] = useState<string[]>([]);
  const [eligibleCoursesData, setEligibleCoursesData] = useState<Course[]>([]);
  const [isLoadingEligibleCourses, setIsLoadingEligibleCourses] = useState(false);

  // Mock user profile data
  const userProfile = {
    name: 'Alex Johnson',
    email: 'alex.johnson@uwaterloo.ca',
    studentId: '20123456',
    program: 'Management Engineering',
    term: '3A',
    completedCredits: 15,
    totalCredits: 40
  };

  // Filter programs based on search
  const filteredPrograms = useMemo(() => {
    if (!programSearch.trim()) return uwPrograms;
    return uwPrograms.filter(program => 
      program.toLowerCase().includes(programSearch.toLowerCase())
    );
  }, [programSearch]);

  // Use the full course data from API
  const eligibleCourses = useMemo(() => {
    return eligibleCoursesData;
  }, [eligibleCoursesData]);

  // Search results from Python search engine
  const [searchResults, setSearchResults] = useState<CourseWithScore[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Search courses using Python search engine
  const searchCourses = async (query: string) => {
    if (!query.trim() || eligibleCourseCodes.length === 0) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch('http://localhost:5001/search-courses', {
        method: 'POST',
        mode: 'cors',
        credentials: 'omit',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          eligible_course_codes: eligibleCourseCodes
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Convert search results to CourseWithScore format
      const results: CourseWithScore[] = data.results.map((result: any) => ({
        course: {
          code: result.code,
          title: result.title || `${result.code} Course`,
          description: result.description || `Description for ${result.code}`
        },
        score: result.score
      }));

      setSearchResults(results);
    } catch (error) {
      console.error('Error searching courses:', error);
      toast({ 
        title: "Error searching courses", 
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive"
      });
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Handle search submission
  const handleSearch = () => {
    if (searchQuery.trim().length >= 2) {
      setHasSearched(true);
      setExecutedSearchQuery(searchQuery.trim());
      searchCourses(searchQuery);
    } else {
      setSearchResults([]);
      setHasSearched(false);
      setExecutedSearchQuery('');
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const fetchEligibleCourses = async () => {
    setIsLoadingEligibleCourses(true);
    try {
      const response = await fetch('http://localhost:5001/get-eligible-courses', {
        method: 'POST',
        mode: 'cors',
        credentials: 'omit',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          program: selections.program,
          term: selections.academicTerm,
          minor: selections.minor || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setEligibleCourseCodes(data.courses.map((c: any) => c.code) || []);
      setEligibleCoursesData(data.courses || []);
    } catch (error) {
      console.error('Error fetching eligible courses:', error);
      toast({ 
        title: "Error fetching courses", 
        description: error instanceof Error ? error.message : "Please try again or check your selections.",
        variant: "destructive"
      });
    } finally {
      setIsLoadingEligibleCourses(false);
    }
  };

  const handleNext = async () => {
    if (currentStep === 1 && !selections.program) {
      toast({ title: "Please select your program", variant: "destructive" });
      return;
    }
    if (currentStep === 2 && !selections.academicTerm) {
      toast({ title: "Please select your academic term", variant: "destructive" });
      return;
    }

    // When moving from Step 3 to Step 4, fetch eligible courses
    if (currentStep === 3) {
      await fetchEligibleCourses();
    }

    if (currentStep === 4 && !userChoice) {
      toast({ title: "Please choose how you'd like to view courses", variant: "destructive" });
      return;
    }
    setCurrentStep(prev => Math.min(prev + 1, 5));
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const resetTool = () => {
    setCurrentStep(1);
    setSelections({ program: '', academicTerm: '', minor: '' });
    setSearchQuery('');
    setExecutedSearchQuery('');
    setUserChoice('');
    setExpandedCourse(null);
    setProgramSearch('');
    setEligibleCourseCodes([]);
    setEligibleCoursesData([]);
  };

  const ProfileDialog = () => (
    <Dialog open={showProfile} onOpenChange={setShowProfile}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            Student Profile
          </DialogTitle>
          <DialogDescription>Your academic information and progress</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Name</label>
              <p className="text-lg font-semibold">{userProfile.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Student ID</label>
              <p className="text-lg font-mono">{userProfile.studentId}</p>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-600">Email</label>
            <p className="text-base">{userProfile.email}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Program</label>
              <p className="text-base">{userProfile.program}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Current Term</label>
              <p className="text-base">{userProfile.term}</p>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-600">Academic Progress</label>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-yellow-400 h-2 rounded-full" 
                  style={{ width: `${(userProfile.completedCredits / userProfile.totalCredits) * 100}%` }}
                />
              </div>
              <span className="text-sm">{userProfile.completedCredits}/{userProfile.totalCredits} credits</span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  const SettingsDialog = () => (
    <Dialog open={showSettings} onOpenChange={setShowSettings}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Settings
          </DialogTitle>
          <DialogDescription>Customize your course selection experience</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Notifications</label>
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4" />
                <span>Course enrollment reminders</span>
              </div>
              <input type="checkbox" defaultChecked className="rounded" />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Display Preferences</label>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <span>Show course descriptions by default</span>
                <input type="checkbox" defaultChecked className="rounded" />
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <span>Highlight prerequisite courses</span>
                <input type="checkbox" defaultChecked className="rounded" />
              </div>
            </div>
          </div>
          <div className="pt-4 border-t">
            <Button variant="outline" className="w-full flex items-center gap-2">
              <LogOut className="w-4 h-4" />
              Sign Out
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );

  const renderStepIndicator = () => (
    <div className="flex items-center justify-center mb-8">
      {[1, 2, 3, 4, 5].map((step) => (
        <React.Fragment key={step}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
            step <= currentStep ? 'bg-yellow-400 text-black' : 'bg-gray-200 text-gray-500'
          }`}>
            {step}
          </div>
          {step < 5 && (
            <div className={`w-12 h-1 ${
              step < currentStep ? 'bg-yellow-400' : 'bg-gray-200'
            }`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );

  // Compute normalized search results (score out of 10)
  const normalizedSearchResults = useMemo(() => {
    if (!searchResults.length) return [];
    const maxScore = Math.max(...searchResults.map(r => r.score));
    if (maxScore === 0) return searchResults.map(r => ({ ...r, normalizedScore: 0 }));
    return searchResults.map(r => ({
      ...r,
      normalizedScore: Math.round((r.score / maxScore) * 10)
    }));
  }, [searchResults]);

  const renderCourseCard = (courseData: CourseWithScore & { normalizedScore?: number }) => {
    const { course, score, normalizedScore } = courseData;
    const isExpanded = expandedCourse === course.code;
    
    return (
      <Card key={course.code} className="hover:shadow-lg transition-all duration-200 border-l-4 border-l-yellow-400">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="font-mono">{course.code.replace(/_/g, ' ')}</Badge>
              {typeof normalizedScore === 'number' && (
                <div className="flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500 fill-current" />
                  <span className="text-sm text-yellow-600 font-medium">{normalizedScore}/10</span>
                </div>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpandedCourse(isExpanded ? null : course.code)}
            >
              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </Button>
          </div>
          <CardTitle className="text-lg text-blue-900">{course.title}</CardTitle>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>{course.credits || 0.5} credits</span>
            <span>•</span>
            <span>{(course.terms || ['Fall 2025']).join(', ')}</span>
          </div>
        </CardHeader>
        {isExpanded && (
          <CardContent className="pt-0">
            <CardDescription className="text-base leading-relaxed mb-4">
              {course.description}
            </CardDescription>
            {(course.prerequisites || []).length > 0 && (
              <div className="mb-3">
                <h4 className="font-semibold text-sm text-gray-700 mb-2">Prerequisites:</h4>
                <div className="flex flex-wrap gap-2">
                  {course.prerequisites.map(prereq => (
                    <Badge key={prereq} variant="secondary">{prereq}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        )}
      </Card>
    );
  };

  // Clear search query/results when leaving the search page
  React.useEffect(() => {
    if (!(currentStep === 5 && userChoice === 'search')) {
      setSearchQuery('');
      setExecutedSearchQuery('');
      setSearchResults([]);
      setHasSearched(false);
    }
  }, [currentStep, userChoice]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-yellow-50">
      {/* Header with Profile and Settings */}
      <header className="bg-white shadow-sm border-b-2 border-yellow-400">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-yellow-400 rounded-lg flex items-center justify-center">
                <GraduationCap className="w-8 h-8 text-blue-900" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-blue-900">Course Selection Tool</h1>
                <p className="text-sm text-gray-600">University of Waterloo</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowProfile(true)}
                className="flex items-center gap-2"
              >
                <User className="w-4 h-4" />
                Profile
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(true)}
                className="flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {renderStepIndicator()}

        {/* Step 1: Program Selection */}
        {currentStep === 1 && (
          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-blue-900 flex items-center justify-center gap-2">
                <Users className="w-6 h-6" />
                Select Your Program
              </CardTitle>
              <CardDescription>Choose your current academic program</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <Input
                  placeholder="Search for your program..."
                  value={programSearch}
                  onChange={(e) => setProgramSearch(e.target.value)}
                  className="w-full"
                />
                <div className="max-h-60 border rounded-md overflow-y-scroll scrollbar-always-visible">
                  {filteredPrograms.map(program => (
                    <div
                      key={program}
                      className={`p-3 cursor-pointer hover:bg-gray-50 border-b last:border-b-0 ${
                        selections.program === program ? 'bg-yellow-50 border-l-4 border-l-yellow-400' : ''
                      }`}
                      onClick={() => setSelections(prev => ({ ...prev, program }))}
                    >
                      <div className="text-sm font-medium">{program}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex justify-end">
                <Button onClick={handleNext} disabled={!selections.program} className="bg-yellow-400 hover:bg-yellow-500 text-black">
                  Next <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Academic Term Selection */}
        {currentStep === 2 && (
          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-blue-900 flex items-center justify-center gap-2">
                <BookOpen className="w-6 h-6" />
                Select Academic Term
              </CardTitle>
              <CardDescription>What academic term are you in? (e.g., 1A, 2B, 4A)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Select value={selections.academicTerm} onValueChange={(value) => setSelections(prev => ({ ...prev, academicTerm: value }))}>
                <SelectTrigger className="w-full h-12 text-lg">
                  <SelectValue placeholder="Choose your academic term..." />
                </SelectTrigger>
                <SelectContent>
                  {academicTerms.map(term => (
                    <SelectItem key={term} value={term}>{term}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex justify-between">
                <Button variant="outline" onClick={handleBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button onClick={handleNext} disabled={!selections.academicTerm} className="bg-yellow-400 hover:bg-yellow-500 text-black">
                  Next <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Minor/Option Selection */}
        {currentStep === 3 && (
          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-blue-900">Minor or Option (Optional)</CardTitle>
              <CardDescription>Are you pursuing any minor or option?</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <Select value={selections.minor} onValueChange={(value) => setSelections(prev => ({ ...prev, minor: value }))}>
                <SelectTrigger className="w-full h-12 text-lg">
                  <SelectValue placeholder="Choose minor/option (optional)..." />
                </SelectTrigger>
                <SelectContent>
                  {minors.map(minor => (
                    <SelectItem key={minor} value={minor}>{minor}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex justify-between">
                <Button variant="outline" onClick={handleBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button 
                  onClick={handleNext} 
                  disabled={isLoadingEligibleCourses}
                  className="bg-yellow-400 hover:bg-yellow-500 text-black"
                >
                  {isLoadingEligibleCourses ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black mr-2"></div>
                      Finding Courses...
                    </>
                  ) : (
                    <>
                      Next <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Eligibility Summary and Choice */}
        {currentStep === 4 && (
          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-blue-900">Course Eligibility Summary</CardTitle>
              <CardDescription>Based on your selections, here's what we found</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Eligibility Summary */}
              <div className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-black p-6 rounded-lg">
                <div className="text-center">
                  {isLoadingEligibleCourses ? (
                    <div>
                      <h3 className="text-xl font-bold mb-2">Finding your eligible courses...</h3>
                      <p className="text-sm opacity-90">Please wait while we analyze your requirements</p>
                    </div>
                  ) : (
                    <div>
                      <h3 className="text-xl font-bold mb-2">
                        You are eligible for <span className="text-3xl font-bold">{eligibleCourseCodes.length}</span> courses
                      </h3>
                      <p className="text-sm opacity-90">
                        {selections.program} • {selections.academicTerm}
                        {selections.minor && selections.minor !== 'None' && ` • ${selections.minor}`}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Choice Buttons */}
              <div className="space-y-4">
                <p className="text-center text-gray-600">How would you like to view your eligible courses?</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button
                    variant={userChoice === 'show-all' ? 'default' : 'outline'}
                    onClick={() => setUserChoice('show-all')}
                    className={`h-20 flex flex-col items-center justify-center gap-2 ${
                      userChoice === 'show-all' ? 'bg-yellow-400 hover:bg-yellow-500 text-black' : ''
                    }`}
                  >
                    <BookOpen className="w-6 h-6" />
                    <span className="font-semibold">Show All Courses</span>
                    <span className="text-xs opacity-75">See the complete list</span>
                  </Button>
                  <Button
                    variant={userChoice === 'search' ? 'default' : 'outline'}
                    onClick={() => setUserChoice('search')}
                    className={`h-20 flex flex-col items-center justify-center gap-2 ${
                      userChoice === 'search' ? 'bg-yellow-400 hover:bg-yellow-500 text-black' : ''
                    }`}
                  >
                    <Search className="w-6 h-6" />
                    <span className="font-semibold">Search with Keywords</span>
                    <span className="text-xs opacity-75">Natural language search</span>
                  </Button>
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={handleBack}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button onClick={handleNext} disabled={!userChoice} className="bg-yellow-400 hover:bg-yellow-500 text-black">
                  Next <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 5: Course Results */}
        {currentStep === 5 && (
          <div className="space-y-6">
            {userChoice === 'show-all' ? (
              // Show All Courses Mode
              <>
                {/* Results Summary */}
                <Card className="shadow-xl bg-gradient-to-r from-yellow-400 to-yellow-500 text-black">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold mb-2">All Eligible Courses</h2>
                      <p className="text-lg">
                        Showing all <span className="font-bold text-2xl">{eligibleCourses.length}</span> courses you can take
                      </p>
                      <p className="text-sm opacity-90 mt-1">
                        {selections.program} • {selections.academicTerm}
                        {selections.minor && selections.minor !== 'None' && ` • ${selections.minor}`}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Course List */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-semibold text-blue-900">
                      Your Eligible Courses ({eligibleCourses.length})
                    </h3>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={handleBack}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back
                      </Button>
                      <Button variant="outline" size="sm" onClick={resetTool}>
                        Start Over
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-4">
                    {eligibleCourses.map(course => renderCourseCard({ course, score: 0 }))}
                  </div>
                </div>
              </>
            ) : (
              // Search Mode
              <>
                {/* Search Interface */}
                <Card className="shadow-xl bg-gradient-to-r from-yellow-400 to-yellow-500 text-black">
                  <CardContent className="pt-6">
                    <div className="text-center">
                      <h2 className="text-2xl font-bold mb-2">Search Your Eligible Courses</h2>
                      <p className="text-lg">
                        Search through your <span className="font-bold text-2xl">{eligibleCourses.length}</span> eligible courses
                      </p>
                      <p className="text-sm opacity-90 mt-1">
                        Natural language search with relevance ratings
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Search Input */}
                <Card className="shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-blue-900">
                      <Search className="w-5 h-5" />
                      Search with Natural Language
                    </CardTitle>
                    <CardDescription>
                      Use keywords to find courses that match your interests
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-3">
                      <Input
                        placeholder="e.g., 'machine learning', 'calculus', 'programming with applications'..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyPress={handleKeyPress}
                        className="flex-1 h-12"
                        disabled={isSearching}
                      />
                      <Button 
                        onClick={handleSearch}
                        disabled={isSearching || !searchQuery.trim()}
                        className="bg-yellow-400 hover:bg-yellow-500 text-black whitespace-nowrap"
                      >
                        {isSearching ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-black mr-2"></div>
                            Searching...
                          </>
                        ) : (
                          <>
                            <Search className="w-4 h-4 mr-2" />
                            Search
                          </>
                        )}
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => {
                          setSearchQuery('');
                          setSearchResults([]);
                          setHasSearched(false);
                          setExecutedSearchQuery('');
                        }}
                        className="whitespace-nowrap"
                        disabled={isSearching}
                      >
                        Clear
                      </Button>
                    </div>
                    {isSearching && (
                      <div className="flex items-center gap-2 text-sm text-blue-600">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        Searching with AI-powered relevance scoring...
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Search Results */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-semibold text-blue-900">
                      {hasSearched ? `Search Results (${searchResults.length})` : `Enter a search term above`}
                    </h3>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={handleBack}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back
                      </Button>
                      <Button variant="outline" size="sm" onClick={resetTool}>
                        Start Over
                      </Button>
                    </div>
                  </div>

                  {isSearching ? (
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="pt-6">
                        <div className="flex items-center justify-center gap-2">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                          <p className="text-sm text-blue-800">Searching with AI-powered relevance scoring...</p>
                        </div>
                      </CardContent>
                    </Card>
                  ) : searchResults.length > 0 ? (
                    <div className="space-y-4">
                      <div className="text-sm text-gray-600 mb-2">
                        Found {searchResults.length} relevant courses for "{executedSearchQuery}" (sorted by relevance score)
                      </div>
                      {normalizedSearchResults.map(renderCourseCard)}
                    </div>
                  ) : hasSearched && executedSearchQuery && !isSearching ? (
                    <Card className="bg-yellow-50 border-yellow-200">
                      <CardContent className="pt-6">
                        <p className="text-sm text-yellow-800 text-center">
                          No matches found for "{executedSearchQuery}". Try different keywords or check your spelling.
                        </p>
                      </CardContent>
                    </Card>
                  ) : (
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="pt-6">
                        <p className="text-sm text-blue-800 text-center">
                          Results from your list of eligible courses will appear here.
                        </p>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </main>

      {/* Profile and Settings Dialogs */}
      <ProfileDialog />
      <SettingsDialog />
    </div>
  );
};

export default Index;
