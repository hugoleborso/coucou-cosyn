export type Part = 'title' | 'artist'

export interface Track {
  order: number
  title: string
  titleAliases: string[]
  artist: string
  artistAliases: string[]
  coverStyle: string
}

export interface Claim {
  round: number
  part: Part
  team: string
  rank: number
}
