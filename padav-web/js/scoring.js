/**
 * Pure scoring logic. The config (marks, negative marks) comes from the quiz definition,
 * never from hardcoded values.
 *
 * @param {{marksPerQuestion:number, negativeMarks:number}} config
 * @param {{selectedKey:?string, correctKey:string}[]} answers selectedKey is null when unanswered
 */
export function evaluate(config, answers) {
  let correct = 0;
  let incorrect = 0;
  let unanswered = 0;
  for (const a of answers) {
    if (a.selectedKey == null) unanswered++;
    else if (a.selectedKey === a.correctKey) correct++;
    else incorrect++;
  }
  const attempted = correct + incorrect;
  return {
    correct,
    incorrect,
    unanswered,
    score: correct * config.marksPerQuestion - incorrect * config.negativeMarks,
    maxScore: answers.length * config.marksPerQuestion,
    accuracy: attempted === 0 ? 0 : correct / attempted,
  };
}
