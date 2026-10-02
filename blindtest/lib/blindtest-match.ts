import type { Part, Track } from './blindtest-types'

const LEADING_ARTICLE = /^(the|le|la|les|l)\s+/
const SHORT_ANSWER_MAX_LENGTH = 4
const CHARACTERS_PER_ALLOWED_TYPO = 5

export function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(LEADING_ARTICLE, '')
}

export function levenshtein(left: string, right: string): number {
  let previous = Array.from({ length: right.length + 1 }, (_, index) => index)
  for (let row = 1; row <= left.length; row++) {
    const current = [row]
    for (let column = 1; column <= right.length; column++) {
      const substitution = previous[column - 1] + (left[row - 1] === right[column - 1] ? 0 : 1)
      current.push(Math.min(previous[column] + 1, current[column - 1] + 1, substitution))
    }
    previous = current
  }
  return previous[right.length]
}

function windows(words: string[], size: number): string[] {
  const result: string[] = []
  for (let start = 0; start + size <= words.length; start++) {
    result.push(words.slice(start, start + size).join(' '))
  }
  return result
}

function matchesAnswer(normalizedGuess: string, answer: string): boolean {
  const target = normalize(answer)
  if (target === '') return false
  const guessWords = normalizedGuess.split(' ')
  const targetWordCount = target.split(' ').length
  if (windows(guessWords, targetWordCount).includes(target)) return true
  if (target.length <= SHORT_ANSWER_MAX_LENGTH) return false
  const allowedTypos = Math.floor(target.length / CHARACTERS_PER_ALLOWED_TYPO)
  const candidateSizes = [targetWordCount - 1, targetWordCount, targetWordCount + 1].filter((size) => size > 0)
  return candidateSizes
    .flatMap((size) => windows(guessWords, size))
    .some((candidate) => levenshtein(candidate, target) <= allowedTypos)
}

export function acceptedAnswers(track: Track, part: Part): string[] {
  return part === 'title' ? [track.title, ...track.titleAliases] : [track.artist, ...track.artistAliases]
}

export function matchedParts(guess: string, track: Track): Part[] {
  const normalizedGuess = normalize(guess)
  const parts: Part[] = ['title', 'artist']
  return parts.filter((part) => acceptedAnswers(track, part).some((answer) => matchesAnswer(normalizedGuess, answer)))
}
