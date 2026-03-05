import styles from './Button.module.css'

type Props = {
  children: React.ReactNode
  variant?: 'primary' | 'ghost' | 'danger'
  type?: 'button' | 'submit'
  disabled?: boolean
  onClick?: () => void
}

export default function Button({
  children,
  variant = 'primary',
  type = 'button',
  disabled,
  onClick,
}: Props) {
  const cls =
    variant === 'primary' ? styles.primary : variant === 'danger' ? styles.danger : styles.ghost

  return (
    <button className={cls} type={type} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  )
}
