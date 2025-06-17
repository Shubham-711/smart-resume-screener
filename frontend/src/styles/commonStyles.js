// frontend/src/styles/commonStyles.js
import { alpha } from '@mui/material/styles';

export const glassMorphismPaperSx = (theme) => ({
  // backgroundColor: alpha(theme.palette.background.paper, 0.65), // Theme now sets paper bg
  // We want a more pronounced glass effect than default paper:
  backgroundColor: alpha(theme.palette.common.black, 0.45), // More transparent black
  backdropFilter: 'blur(12px)', // More blur
  WebkitBackdropFilter: 'blur(12px)',
  border: `1px solid ${alpha(theme.palette.common.white, 0.18)}`, // Slightly more visible border
  borderRadius: theme.shape.borderRadius, // Use theme's border radius (10px)
  // boxShadow: `0 8px 32px 0 ${alpha(theme.palette.common.black, 0.37)}`, // Can be subtle
  padding: theme.spacing(3),
  color: theme.palette.text.primary,
});

export const glowButtonSx = (theme, color = 'primary') => ({
  fontWeight: 'bold',
  color: theme.palette.getContrastText(theme.palette[color].main),
  backgroundColor: theme.palette[color].main,
  padding: theme.spacing(1.25, 3), // py, px
  // borderRadius is handled by MuiButton global override if you want all buttons same
  transition: theme.transitions.create(['background-color', 'box-shadow', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  boxShadow: `0 0 5px ${alpha(theme.palette[color].main, 0.4)}, 0 0 10px ${alpha(theme.palette[color].main, 0.2)}`,
  '&:hover': {
    backgroundColor: theme.palette[color].light,
    boxShadow: `0 0 12px ${alpha(theme.palette[color].light, 0.6)}, 0 0 25px ${alpha(theme.palette[color].light, 0.4)}`,
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0px)',
    boxShadow: `0 0 3px ${alpha(theme.palette[color].main, 0.5)}`,
  },
  '&.Mui-disabled': {
    boxShadow: 'none',
    backgroundColor: theme.palette.action.disabledBackground,
    color: theme.palette.action.disabled,
  }
});

export const glassMorphismSx = (theme) => ({
  backdropFilter: 'blur(10px)',
  background: 'rgba(255, 255, 255, 0.05)',
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: '20px',
  padding: '2rem',
  boxShadow: theme.shadows[8],
});
