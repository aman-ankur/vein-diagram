/**
 * QuickQuestions - Suggested questions for easy chat interaction
 */
import React from 'react';
import { SuggestedQuestion } from '../../types/chat';
import { MessageSquare, TrendingUp, Heart, Activity, Zap } from 'lucide-react';

interface QuickQuestionsProps {
  questions: SuggestedQuestion[];
  onQuestionClick: (question: string) => void;
  disabled?: boolean;
  className?: string;
}

const categoryIcons = {
  abnormal: TrendingUp,
  favorites: Heart,
  general: MessageSquare,
  health_score: Activity
};

const categoryColors = {
  abnormal: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
  favorites: 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
  general: 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100',
  health_score: 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
};

const categoryLabels = {
  abnormal: 'Abnormal Values',
  favorites: 'Your Favorites',
  general: 'General Health',
  health_score: 'Health Score'
};

export const QuickQuestions: React.FC<QuickQuestionsProps> = ({
  questions,
  onQuestionClick,
  disabled = false,
  className = ''
}) => {
  if (questions.length === 0) {
    return null;
  }

  // Sort questions by priority and group by category
  const sortedQuestions = [...questions].sort((a, b) => a.priority - b.priority);
  const groupedQuestions = sortedQuestions.reduce((acc, question) => {
    if (!acc[question.category]) {
      acc[question.category] = [];
    }
    acc[question.category].push(question);
    return acc;
  }, {} as Record<string, SuggestedQuestion[]>);

  return (
    <div className={`bg-white border-b border-gray-200 p-4 max-h-60 overflow-y-auto ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900 flex items-center">
          <Zap className="w-4 h-4 mr-2 text-yellow-500" />
          Quick Questions
        </h3>
        <span className="text-xs text-gray-500">
          {questions.length} suggestion{questions.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="space-y-3">
        {Object.entries(groupedQuestions).map(([category, categoryQuestions]) => {
          const Icon = categoryIcons[category as keyof typeof categoryIcons];
          const colorClass = categoryColors[category as keyof typeof categoryColors];
          const label = categoryLabels[category as keyof typeof categoryLabels];

          return (
            <div key={category} className="space-y-2">
              {/* Category Header */}
              <div className="flex items-center text-xs text-gray-600">
                <Icon className="w-3 h-3 mr-1" />
                {label}
              </div>

              {/* Questions in Category */}
              <div className="space-y-2">
                {categoryQuestions.map((question, index) => (
                  <button
                    key={`${category}-${index}`}
                    onClick={() => onQuestionClick(question.question)}
                    disabled={disabled}
                    className={`
                      w-full text-left p-3 rounded-lg border text-sm
                      transition-all duration-200 transform hover:scale-[1.02]
                      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                      ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                      ${colorClass}
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <span className="flex-1 pr-2">{question.question}</span>
                      {category === 'abnormal' && (
                        <div className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full mt-1.5"></div>
                      )}
                      {category === 'favorites' && (
                        <Heart className="flex-shrink-0 w-3 h-3 mt-0.5 fill-current" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Helpful Tips */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-start space-x-2">
          <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
          <div className="text-xs text-blue-700">
            <strong>Tip:</strong> These questions are personalized based on your biomarker results. 
            Click any question to start the conversation, or type your own question below.
          </div>
        </div>
      </div>
    </div>
  );
}; 