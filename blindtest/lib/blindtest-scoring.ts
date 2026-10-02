import type { Claim } from './blindtest-types'

const POINTS_FOR_FIRST = 10
const MINIMUM_POINTS = 1
const PARTS_PER_TRACK = 2

export function pointsForRank(rank: number): number {
  return Math.max(MINIMUM_POINTS, POINTS_FOR_FIRST + 1 - rank) / PARTS_PER_TRACK
}

export function teamTotals(claims: Claim[]): Map<string, number> {
  const totals = new Map<string, number>()
  for (const claim of claims) {
    totals.set(claim.team, (totals.get(claim.team) ?? 0) + pointsForRank(claim.rank))
  }
  return totals
}

export function ranking(claims: Claim[]): { team: string; points: number }[] {
  return [...teamTotals(claims)]
    .map(([team, points]) => ({ team, points }))
    .sort((left, right) => right.points - left.points || left.team.localeCompare(right.team))
}
