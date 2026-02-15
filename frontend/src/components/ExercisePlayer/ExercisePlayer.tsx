import React, { useEffect, useState } from 'react'
import Button from '../../components/ui/Button/Button'
import { Card } from '../../components/ui/Card/Card'
import type { Exercise, QuizExercise, MatchExercise, TrueFalseExercise, FillBlankExercise, ScrambleExercise } from '../../api/lessons'
import styles from './ExercisePlayer.module.css'

interface ExercisePlayerProps {
  exercises: Exercise[]
  onComplete: (results: ExerciseResult[]) => void
}

interface ExerciseResult {
  exerciseIndex: number
  type: string
  correct: boolean
  userAnswer?: any
}

// Компоненты для каждого типа упражнения
interface QuizExerciseViewProps {
  exercise: QuizExercise
  index: number
  onAnswer: (i: number, a: number) => void
}

function QuizExerciseView({ exercise, index, onAnswer }: QuizExerciseViewProps) {
  const [selected, setSelected] = useState<number | null>(null)
  const [isWrong, setIsWrong] = useState(false)
  const [showCorrect, setShowCorrect] = useState(false)

  const handleSubmit = () => {
    if (selected === null) return
    
    const correct = selected === exercise.correct_index
    if (!correct) {
      setIsWrong(true)
      setTimeout(() => setIsWrong(false), 500)
    } else {
      setShowCorrect(true)
      setTimeout(() => onAnswer(index, selected), 800)
    }
  }

  return (
    <div title={`Вопрос ${index + 1}`}>
      <p className={styles.question}>{exercise.question}</p>
      <div className={styles.options}>
        {exercise.options.map((opt, i) => (
          <label
            key={i}
            className={`${styles.optionLabel} ${
              selected === i ? (showCorrect ? styles.correct : isWrong ? styles.wrong : styles.selected) : ''
            } ${showCorrect && i === exercise.correct_index ? styles.correct : ''}`}
          >
            <input
              type="radio"
              name={`quiz-${index}`}
              value={i}
              checked={selected === i}
              onChange={() => setSelected(i)}
              disabled={showCorrect}
            />
            <span>{opt} {showCorrect && i === exercise.correct_index && '✓'} {isWrong && selected === i && '✗'}</span>
          </label>
        ))}
      </div>
      <Button onClick={handleSubmit} disabled={selected === null || showCorrect}>
        Ответить
      </Button>
    </div>
  )
}

function MatchExerciseView({ exercise, index, onAnswer }: { exercise: MatchExercise; index: number; onAnswer: (i: number, a: string[][]) => void }) {
  const [pairs, setPairs] = useState<string[][]>([])
  const [isWrong, setIsWrong] = useState(false)
  const [showCorrect, setShowCorrect] = useState(false)

  const handleDrop = (fromIdx: number, toIdx: number) => {
    const newPairs = [...pairs]
    const [moved] = newPairs.splice(fromIdx, 1)
    newPairs.splice(toIdx, 0, moved)
    setPairs(newPairs)
  }

  const handleSubmit = () => {
    const correct = pairs.every(([left, right]) => {
      const pair = exercise.pairs.find(p => p.left === left)
      return pair && pair.right === right
    })
    if (!correct) {
      setIsWrong(true)
      setShowCorrect(true)
      setTimeout(() => {
        setIsWrong(false)
        setShowCorrect(false)
      }, 2000)
    } else {
      setShowCorrect(true)
      setTimeout(() => onAnswer(index, pairs), 800)
    }
  }

  useEffect(() => {
    // Shuffle right side initially
    const shuffled = exercise.pairs.map(p => [p.left, p.right]).sort(() => Math.random() - 0.5)
    setPairs(shuffled)
  }, [exercise])

  return (
    <div title={`Сопоставление ${index + 1}`}>
      <div className={styles.matchContainer}>
        <div className={styles.column}>
          <h4>Левая колонка</h4>
          {exercise.pairs.map((p, i) => (
            <div key={i} className={styles.matchItem}>{p.left}</div>
          ))}
        </div>
        <div className={styles.column}>
          <h4>Правая колонка (перетащите)</h4>
          {(showCorrect && !isWrong ? exercise.pairs.map(p => [p.left, p.right]) : pairs).map((pair, i) => (
            <div
              key={i}
              draggable={!showCorrect && !isWrong}
              onDragStart={(e) => e.dataTransfer.setData('text/plain', i.toString())}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault()
                const fromIdx = parseInt(e.dataTransfer.getData('text/plain'), 10)
                handleDrop(fromIdx, i)
              }}
              className={`${styles.matchItem} ${isWrong ? styles.wrong : ''} ${showCorrect ? styles.correct : ''}`}
              style={{
                cursor: showCorrect || isWrong ? 'not-allowed' : 'move',
                opacity: showCorrect || isWrong ? 0.7 : 1
              }}
            >
              {pair[1]}
            </div>
          ))}
        </div>
      </div>
      <Button onClick={handleSubmit} disabled={showCorrect || isWrong}>Проверить</Button>
    </div>
  )
}

function TrueFalseExerciseView({ exercise, index, onAnswer }: { exercise: TrueFalseExercise; index: number; onAnswer: (i: number, a: boolean) => void }) {
  const [selected, setSelected] = useState<boolean | null>(null)
  const [isWrong, setIsWrong] = useState(false)
  const [showCorrect, setShowCorrect] = useState(false)

  const handleSubmit = () => {
    if (selected === null) return
    
    const correct = selected === exercise.is_true
    if (!correct) {
      setIsWrong(true)
      setShowCorrect(true)
      setTimeout(() => {
        setIsWrong(false)
        setShowCorrect(false)
      }, 2000)
    } else {
      setShowCorrect(true)
      setTimeout(() => onAnswer(index, selected), 800)
    }
  }

  return (
    <div title={`Верно/Неверно ${index + 1}`}>
      <p className={styles.statement}>{exercise.statement}</p>
      <div className={styles.tfOptions}>
        <label className={`${styles.tfLabel} ${
          selected === true ? (showCorrect ? styles.correct : isWrong ? styles.wrong : styles.selected) : ''
        } ${
          showCorrect && exercise.is_true === true ? styles.correct : ''
        } ${
          isWrong && selected === true ? styles.wrong : ''
        }`}>
          <input
            type="radio"
            name={`tf-${index}`}
            checked={selected === true}
            onChange={() => setSelected(true)}
            disabled={showCorrect || isWrong}
          />
          <span>Верно {showCorrect && exercise.is_true === true && '✓'} {isWrong && selected === true && '✗'}</span>
        </label>
        <label className={`${styles.tfLabel} ${
          selected === false ? (showCorrect ? styles.correct : isWrong ? styles.wrong : styles.selected) : ''
        } ${
          showCorrect && exercise.is_true === false ? styles.correct : ''
        } ${
          isWrong && selected === false ? styles.wrong : ''
        }`}>
          <input
            type="radio"
            name={`tf-${index}`}
            checked={selected === false}
            onChange={() => setSelected(false)}
            disabled={showCorrect || isWrong}
          />
          <span>Неверно {showCorrect && exercise.is_true === false && '✓'} {isWrong && selected === false && '✗'}</span>
        </label>
      </div>
      <Button onClick={handleSubmit} disabled={selected === null || showCorrect || isWrong}>
        Ответить
      </Button>
    </div>
  )
}

function FillBlankExerciseView({ exercise, index, onAnswer }: { exercise: FillBlankExercise; index: number; onAnswer: (i: number, a: string) => void }) {
  const [answer, setAnswer] = useState('')
  const [isWrong, setIsWrong] = useState(false)
  const [showCorrect, setShowCorrect] = useState(false)
  const [showHint, setShowHint] = useState(false)

  const handleSubmit = () => {
    if (!answer.trim()) return
    
    const correct = answer.toLowerCase() === exercise.correct_word.toLowerCase()
    if (!correct) {
      setIsWrong(true)
      setShowCorrect(true)
      setTimeout(() => {
        setIsWrong(false)
        setShowCorrect(false)
      }, 2000)
    } else {
      setShowCorrect(true)
      setTimeout(() => onAnswer(index, answer.trim()), 800)
    }
  }

  const handleHint = () => {
    setShowHint(true)
  }

  return (
    <div title={`Заполните пропуск ${index + 1}`}>
      <p className={styles.sentence}>
        {exercise.sentence.split('___').map((part, idx, arr) => (
          <React.Fragment key={idx}>
            {part}
            {idx < arr.length - 1 && (
              <>
                <input
                  className={`${styles.blankInput} ${
                    showCorrect ? styles.correct : isWrong ? styles.wrong : ''
                  }`}
                  value={showCorrect && !isWrong ? exercise.correct_word : answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={showCorrect || isWrong}
                />
                {showHint && !showCorrect && (
                  <span className={styles.hint}>
                    Подсказка: {exercise.correct_word}
                  </span>
                )}
              </>
            )}
          </React.Fragment>
        ))}
      </p>
      <div className={styles.controls}>
        <Button onClick={handleSubmit} disabled={!answer.trim() || showCorrect || isWrong}>
          Ответить
        </Button>
        <Button onClick={handleHint} disabled={showHint || showCorrect || isWrong} variant="secondary">
          {showHint ? 'Подсказка использована' : 'Подсказка'}
        </Button>
      </div>
    </div>
  )
}

function ScrambleExerciseView({ exercise, index, onAnswer }: { exercise: ScrambleExercise; index: number; onAnswer: (i: number, a: string[]) => void }) {
  const [order, setOrder] = useState<string[]>([])
  const [isWrong, setIsWrong] = useState(false)
  const [showCorrect, setShowCorrect] = useState(false)

  const handleMove = (fromIdx: number, toIdx: number) => {
    const newOrder = [...order]
    const [moved] = newOrder.splice(fromIdx, 1)
    newOrder.splice(toIdx, 0, moved)
    setOrder(newOrder)
  }

  const handleSubmit = () => {
    const correct = order.join(' ') === exercise.correct_sentence
    if (!correct) {
      setIsWrong(true)
      setShowCorrect(true)
      setTimeout(() => {
        setIsWrong(false)
        setShowCorrect(false)
      }, 2000)
    } else {
      setShowCorrect(true)
      setTimeout(() => onAnswer(index, order), 800)
    }
  }

  useEffect(() => {
    // Use scrambled_parts from backend
    if (Array.isArray(exercise.scrambled_parts)) {
      setOrder([...exercise.scrambled_parts])
    }
  }, [exercise])

  return (
    <div title={`Восстановите порядок ${index + 1}`}>
      <div className={`${styles.scrambleContainer} ${isWrong ? styles.wrong : ''} ${showCorrect ? styles.correct : ''}`}>
        {(showCorrect && !isWrong ? exercise.correct_sentence.split(' ') : order).map((word: string, i: number) => (
          <div
            key={i}
            draggable={!showCorrect && !isWrong}
            onDragStart={(e) => e.dataTransfer.setData('text/plain', i.toString())}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              const fromIdx = parseInt(e.dataTransfer.getData('text/plain'), 10)
              handleMove(fromIdx, i)
            }}
            className={styles.scrambleWord}
            style={{
              cursor: showCorrect || isWrong ? 'not-allowed' : 'move',
              opacity: showCorrect || isWrong ? 0.7 : 1
            }}
          >
            {word}
          </div>
        ))}
      </div>
      <Button onClick={handleSubmit} disabled={showCorrect || isWrong}>
        Проверить
      </Button>
    </div>
  )
}

export default function ExercisePlayer({ exercises, onComplete }: ExercisePlayerProps) {
  const [results, setResults] = useState<ExerciseResult[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [showResult, setShowResult] = useState(false)

  const handleAnswer = (exerciseIndex: number, userAnswer: any) => {
    const exercise = exercises[exerciseIndex]
    let correct = false

    switch (exercise.type) {
      case 'quiz':
        correct = userAnswer === exercise.correct_index
        break
      case 'match':
        correct = (userAnswer as string[][]).every(([left, right]) => {
          const pair = exercise.pairs.find(p => p.left === left)
          return pair && pair.right === right
        })
        break
      case 'true_false':
        correct = userAnswer === exercise.is_true
        break
      case 'fill_blank':
        correct = userAnswer.toLowerCase() === exercise.correct_word.toLowerCase()
        break
      case 'scramble':
        correct = (userAnswer as string[]).join(' ') === exercise.correct_sentence
        break
    }

    const newResult: ExerciseResult = { exerciseIndex, type: exercise.type, correct, userAnswer }
    const newResults = [...results, newResult]
    setResults(newResults)

    // Показываем результат сразу после ответа
    if (!correct) {
      // Ничего не делаем, пользователь может попробовать еще раз
      return
    }

    // Верно - переходим к следующему упражнению
    if (exerciseIndex + 1 < exercises.length) {
      setCurrentIdx(exerciseIndex + 1)
    } else {
      onComplete(newResults)
      setShowResult(true)
    }
  }

  const renderExercise = (exercise: Exercise, index: number) => {
    switch (exercise.type) {
      case 'quiz':
        return <QuizExerciseView key={index} exercise={exercise} index={index} onAnswer={handleAnswer} />
      case 'match':
        return <MatchExerciseView key={index} exercise={exercise} index={index} onAnswer={handleAnswer} />
      case 'true_false':
        return <TrueFalseExerciseView key={index} exercise={exercise} index={index} onAnswer={handleAnswer} />
      case 'fill_blank':
        return <FillBlankExerciseView key={index} exercise={exercise} index={index} onAnswer={handleAnswer} />
      case 'scramble':
        return <ScrambleExerciseView key={index} exercise={exercise} index={index} onAnswer={handleAnswer} />
      default:
        return <div>Неизвестный тип упражнения</div>
    }
  }

  if (showResult) {
    const correctCount = results.filter(r => r.correct).length
    return (
      <Card title="Результаты" className={styles.resultsCard}>
        <p>Правильно: {correctCount} / {results.length}</p>
        {results.map((r) => (
          <div key={r.exerciseIndex} className={styles.resultItem}>
            {r.type}: {r.correct ? '✅' : '❌'}
          </div>
        ))}
      </Card>
    )
  }

  return (
    <div className={styles.container}>
      <h2>Упражнения ({currentIdx + 1} / {exercises.length})</h2>
      {renderExercise(exercises[currentIdx], currentIdx)}
    </div>
  )
}
