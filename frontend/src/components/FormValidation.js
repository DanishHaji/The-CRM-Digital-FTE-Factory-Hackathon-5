/**
 * Form Validation Logic
 * Client-side validation for Web Support Form
 */

export const validateEmail = (email) => {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return emailRegex.test(email.trim());
};

export const validateName = (name) => {
  return name.trim().length >= 2;
};

export const validateMessage = (message) => {
  return message.trim().length >= 10;
};

export const validateForm = (formData, t) => {
  const errors = {};

  // Name validation
  if (!formData.name || !formData.name.trim()) {
    errors.name = t.messages.nameRequired;
  } else if (!validateName(formData.name)) {
    errors.name = t.messages.nameRequired;
  }

  // Email validation
  if (!formData.email || !formData.email.trim()) {
    errors.email = t.messages.emailRequired;
  } else if (!validateEmail(formData.email)) {
    errors.email = t.messages.emailInvalid;
  }

  // Message validation
  if (!formData.message || !formData.message.trim()) {
    errors.message = t.messages.messageRequired;
  } else if (!validateMessage(formData.message)) {
    errors.message = t.messages.messageShort;
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const sanitizeInput = (input) => {
  return input.trim().replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
};
