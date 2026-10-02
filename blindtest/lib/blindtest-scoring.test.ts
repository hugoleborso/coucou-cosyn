import { describe, expect, it } from 'vitest'
import { pointsForRank, ranking, teamTotals } from './blindtest-scoring'
import type { Claim } from './blindtest-types'

describe('pointsForRank', () => {
  it('gives 5, 4.5 … down to 0.5 for each part', () => {
    expect(pointsForRank(1)).toBe(5)
    expect(pointsForRank(2)).toBe(4.5)
    expect(pointsForRank(10)).toBe(0.5)
    expect(pointsForRank(11)).toBe(0.5)
    expect(pointsForRank(18)).toBe(0.5)
  })
})

describe('teamTotals and ranking', () => {
  const claims: Claim[] = [
    { round: 1, part: 'title', team: 'B', rank: 1 },
    { round: 1, part: 'artist', team: 'B', rank: 1 },
    { round: 1, part: 'title', team: 'A', rank: 2 },
    { round: 2, part: 'title', team: 'A', rank: 1 },
    { round: 2, part: 'title', team: 'C', rank: 2 },
  ]

  it('sums both parts across rounds', () => {
    expect(teamTotals(claims)).toEqual(new Map([['B', 10], ['A', 9.5], ['C', 4.5]]))
  })

  it('sorts by points, then by team name', () => {
    expect(ranking(claims)).toEqual([
      { team: 'B', points: 10 },
      { team: 'A', points: 9.5 },
      { team: 'C', points: 4.5 },
    ])
    expect(ranking([
      { round: 1, part: 'title', team: 'Z', rank: 1 },
      { round: 1, part: 'artist', team: 'Y', rank: 1 },
    ]).map((entry) => entry.team)).toEqual(['Y', 'Z'])
  })
})
