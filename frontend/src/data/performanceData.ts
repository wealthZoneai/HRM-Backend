export const performanceData = {
  metrics: {
    overallScore: { value: "8.7/10", change: "+5%" },
    tasksCompleted: { value: 52, change: "+12%" },
    ongoingTasks: { value: 2, change: "+10%" },
  },

  weeklyPerformance: [
    { day: "Mon", value: 75 },
    { day: "Tue", value: 100 },
    { day: "Wed", value: 60 },
    { day: "Thu", value: 45 },
    { day: "Fri", value: 15 },
  ],

  objectives: [
    {
      title: "Launch new feature X",
      description:
        "Complete the final development and deployment phase for the new user authentication feature.",
      progress: 70,
    },
  ],

  feedback: [
    {
      manager: "John Smith",
      date: "November 04, 2025",
      message:
        "John’s work on the new feature was outstanding. His attention to detail and proactive communication helped the team stay on track.",
    },
    {
      manager: "David Chen",
      date: "October 15, 2025",
      message:
        "Great improvement in task ownership this month. Continue communicating early when blockers appear.",
    },
    {
      manager: "Sarah Lee",
      date: "September 28, 2025",
      message:
        "Good collaboration with the UI/UX team. Focus more on deadline predictability next sprint.",
    },
  ],
};
