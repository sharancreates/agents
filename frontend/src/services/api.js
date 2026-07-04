import mockSubmissions from '../mockData/submissions.json';

export const fetchSubmissions = async () => {
  // Simulate an 800ms network delay to mimic the real FastAPI backend
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockSubmissions);
    }, 800);
  });
};

export const fetchSubmissionById = async (id) => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const submission = mockSubmissions.find(sub => sub.submission_id === id);
      if (submission) {
        resolve(submission);
      } else {
        reject(new Error("Submission not found"));
      }
    }, 500);
  });
};