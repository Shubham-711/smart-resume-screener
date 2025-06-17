// frontend/src/pages/HomePage.jsx
import React from 'react';
import { Box, Typography, Paper, Button, useTheme } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { motion } from 'framer-motion'; // Import motion
import { glassMorphismSx, glowButtonSx } from '../styles/commonStyles';


// Animation variants for Framer Motion
const containerVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      delay: 0.2,
      staggerChildren: 0.2, // Animate children one after another
      when: "beforeChildren"
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } }
};

function HomePage() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        width: '100%',
        minHeight:'calc(100vh - 64px)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        px: 2,
        py: { xs: 4, sm: 6 },
      }}
    >
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{
          width: '100%',
          maxWidth: '900px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={0}
          component={motion.div}
          variants={itemVariants}
          sx={{
            ...glassMorphismSx(theme),
            p: { xs: 3, sm: 5, md: 6 },
            borderRadius: '40px',
            textAlign: 'center',
            width: '100%',
          }}
        >
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            sx={{
              fontWeight: 800,
              fontSize: { xs: '2rem', sm: '3rem' },
              color: 'primary.light',
              lineHeight: 1.2,
            }}
          >
            Welcome to the Smart <br /> Resume Screener!
          </Typography>

          <Typography
            variant="h6"
            color="text.secondary"
            paragraph
            sx={{ maxWidth: 650, mx: 'auto', mb: 2 }}
          >
            Streamline your hiring process by automatically screening resumes
            against job descriptions. Our AI-powered system helps you identify
            the most relevant candidates quickly and efficiently.
          </Typography>

          <Typography
            variant="body1"
            sx={{ fontWeight: 500, maxWidth: 650, mx: 'auto', mb: 3 }}
          >
            Get started by creating a new job posting or viewing existing ones to
            manage resumes. This tool leverages Natural Language Processing to match
            skills and rank applicants, saving you valuable time.
          </Typography>

          <Box
            component={motion.div}
            variants={itemVariants}
            sx={{
              mt: 4,
              display: 'flex',
              justifyContent: 'center',
              gap: 3,
              flexWrap: 'wrap',
            }}
          >
            <Button
              component={motion(RouterLink)}
              variants={itemVariants}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              to="/create-job"
              variant="contained"
              color="primary"
              size="large"
              sx={glowButtonSx(theme)}
            >
              Create New Job
            </Button>

            <Button
              component={motion(RouterLink)}
              variants={itemVariants}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              to="/jobs"
              variant="outlined"
              color="secondary"
              size="large"
              sx={glowButtonSx(theme, 'secondary')}
            >
              View Job List
            </Button>
          </Box>
        </Paper>
      </motion.div>
    </Box>
  );
}
export default HomePage;