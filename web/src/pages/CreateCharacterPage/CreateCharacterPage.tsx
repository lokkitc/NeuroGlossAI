import { useMutation } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../../components/ui/Card/Card'
import Field from '../../components/ui/Field/Field'
import Button from '../../components/ui/Button/Button'
import * as characters from '../../services/characters'
import { getErrorMessage } from '../../services/http'
import styles from './CreateCharacterPage.module.css'

export default function CreateCharacterPage() {
  const nav = useNavigate()

  const [slug, setSlug] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [stylePrompt, setStylePrompt] = useState('')
  const [greeting, setGreeting] = useState('')
  const [tags, setTags] = useState('')
  const [isPublic, setIsPublic] = useState(true)
  const [isNsfw, setIsNsfw] = useState(false)

  const slugError = useMemo(() => {
    const v = slug.trim()
    if (!v) return 'Required'
    if (v.length > 64) return 'Too long (max 64)'
    return null
  }, [slug])

  const displayNameError = useMemo(() => {
    if (!displayName.trim()) return 'Required'
    return null
  }, [displayName])

  const systemPromptError = useMemo(() => {
    if (!systemPrompt.trim()) return 'Required'
    return null
  }, [systemPrompt])

  const createM = useMutation({
    mutationFn: async () => {
      if (slugError || displayNameError || systemPromptError) {
        throw new Error('Fix validation errors')
      }

      const tagsArr = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)

      return characters.createCharacter({
        slug: slug.trim(),
        display_name: displayName.trim(),
        description: description.trim(),
        system_prompt: systemPrompt.trim(),
        style_prompt: stylePrompt.trim() || null,
        greeting: greeting.trim() || null,
        tags: tagsArr.length ? tagsArr : null,
        is_public: isPublic,
        is_nsfw: isNsfw,
        avatar_url: null,
        thumbnail_url: null,
        banner_url: null,
        voice_provider: null,
        voice_id: null,
        voice_settings: null,
        chat_settings: null,
        chat_theme_id: null,
        settings: null,
      })
    },
    onSuccess: () => {
      nav('/')
    },
  })

  const errMsg = createM.isError ? getErrorMessage(createM.error, 'Failed to create character') : null

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <h1 className={styles.title}>Create character</h1>
        <div className={styles.subtitle}>Create a new persona and start roleplaying immediately.</div>
      </div>

      <Card className={styles.card}>
        <form
          className={styles.form}
          onSubmit={(e) => {
            e.preventDefault()
            createM.mutate()
          }}
        >
          <div className={styles.grid2}>
            <Field label='Slug' hint='Unique id, used in URLs (max 64)' error={slugError}>
              <input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder='e.g. yuki-tutor' />
            </Field>
            <Field label='Display name' error={displayNameError}>
              <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder='e.g. Yuki' />
            </Field>
          </div>

          <Field label='Description' hint='Shown on the Home page'>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder='What is this character about?'
              rows={3}
            />
          </Field>

          <Field label='System prompt' hint='Defines the character behavior' error={systemPromptError}>
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder='You are ...'
              rows={6}
            />
          </Field>

          <Field label='Style prompt' hint='Optional writing style instructions'>
            <textarea
              value={stylePrompt}
              onChange={(e) => setStylePrompt(e.target.value)}
              placeholder='Write in a warm, concise style...'
              rows={3}
            />
          </Field>

          <div className={styles.grid2}>
            <Field label='Greeting' hint='First message the assistant can use'>
              <input value={greeting} onChange={(e) => setGreeting(e.target.value)} placeholder='Hi! I am ...' />
            </Field>
            <Field label='Tags' hint='Comma-separated'>
              <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder='tutor, anime, friendly' />
            </Field>
          </div>

          <div className={styles.toggles}>
            <label className={styles.toggle}>
              <input type='checkbox' checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
              Public
            </label>
            <label className={styles.toggle}>
              <input type='checkbox' checked={isNsfw} onChange={(e) => setIsNsfw(e.target.checked)} />
              NSFW
            </label>
          </div>

          <div className={styles.actions}>
            <Button type='submit' disabled={createM.isPending}>
              {createM.isPending ? 'Creating…' : 'Create'}
            </Button>
          </div>

          {errMsg ? <div className={styles.error}>{errMsg}</div> : null}
        </form>
      </Card>
    </div>
  )
}
