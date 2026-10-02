import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { acceptedAnswers, levenshtein, matchedParts, normalize } from './blindtest-match'
import type { Track } from './blindtest-types'

function loadTracks(): Track[] {
  const [, ...rows] = readFileSync(new URL('../blindtest_tracks.csv', import.meta.url), 'utf8').trim().split('\n')
  return rows.map((row) => {
    const [order, title, titleAliases, artist, artistAliases, coverStyle] = row.split(',')
    const split = (value: string) => value.split(';').filter(Boolean)
    return { order: Number(order), title, titleAliases: split(titleAliases), artist, artistAliases: split(artistAliases), coverStyle }
  })
}

const tracks = loadTracks()
const byTitle = (title: string) => tracks.find((track) => track.title === title)!

describe('normalize', () => {
  it('strips accents, punctuation, case and a leading article', () => {
    expect(normalize('  Les Démons de Minuit !')).toBe('demons de minuit')
    expect(normalize("L'Été indien")).toBe('ete indien')
    expect(normalize('The Eagles')).toBe('eagles')
    expect(normalize('Simon & Garfunkel')).toBe('simon and garfunkel')
  })
})

describe('levenshtein', () => {
  it('counts edits', () => {
    expect(levenshtein('kitten', 'sitting')).toBe(3)
    expect(levenshtein('', 'abc')).toBe(3)
    expect(levenshtein('same', 'same')).toBe(0)
  })
})

describe('matchedParts', () => {
  it.each(tracks.map((track) => [track.title, track]))('accepts the exact title and artist of %s', (_, track) => {
    expect(matchedParts(track.title, track)).toContain('title')
    expect(matchedParts(track.artist, track)).toContain('artist')
  })

  it('finds both parts in one guess, in any order', () => {
    expect(matchedParts('queen bohemian rapsody', byTitle('Bohemian Rhapsody'))).toEqual(['title', 'artist'])
  })

  it('tolerates typos in proportion to the answer length', () => {
    expect(matchedParts('smels like teen spirt', byTitle('Smells Like Teen Spirit'))).toEqual(['title'])
    expect(matchedParts('eminen', byTitle('Lose Yourself'))).toEqual(['artist'])
    expect(matchedParts('johny haliday', byTitle('Allumer le feu'))).toEqual(['artist'])
  })

  it('accepts aliases', () => {
    expect(matchedParts('rhcp', byTitle('Under the Bridge'))).toEqual(['artist'])
    expect(matchedParts("i'm blue", byTitle('Blue (Da Ba Dee)'))).toEqual(['title'])
    expect(matchedParts('cloclo', byTitle('Alexandrie Alexandra'))).toEqual(['artist'])
  })

  it('requires short answers to match exactly', () => {
    const gimme = byTitle('Gimme! Gimme! Gimme!')
    expect(matchedParts('abba', gimme)).toEqual(['artist'])
    expect(matchedParts('abda', gimme)).toEqual([])
  })

  it('rejects an unrelated guess', () => {
    expect(matchedParts('get lucky daft punk', byTitle('Skyfall'))).toEqual([])
  })

  it('ignores empty aliases', () => {
    const track = { ...byTitle('Skyfall'), artistAliases: ['!!!'] }
    expect(matchedParts('???', track)).toEqual([])
  })
})

describe('acceptedAnswers', () => {
  it('lists the canonical answer first', () => {
    expect(acceptedAnswers(byTitle('Lose Yourself'), 'artist')).toEqual(['Eminem', 'Slim Shady', 'Marshall Mathers'])
  })
})
