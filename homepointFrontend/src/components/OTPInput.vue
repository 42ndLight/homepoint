<template>
  <div ref="otpCont" class="flex justify-between w-full mx-auto gap-2">
    <input
      :id="`otpcode-${ind}`"
      type="text"
      class="w-12 h-14 border-2 border-gray-300 rounded-lg text-center text-2xl font-bold text-gray-800 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:outline-none transition-all duration-200"
      :class="{ 'animate-bounce-short': digits[ind] !== null }"
      v-for="(el, ind) in digits"
      :key="el+ind"
      v-model="digits[ind]"
      :autofocus="ind === 0"
      maxlength="1"
      @keydown="handleKeyDown($event, ind)"
      @paste="handlePaste"
    >
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const props = defineProps({
  default: String,
  digitCount: {
    type: Number,
    default: 6
  }
})

const emit = defineEmits(['update:otp'])

const digits = reactive([])

if (props.default && props.default.length === props.digitCount) {
  for (let i = 0; i < props.digitCount; i++) {
    digits[i] = props.default.charAt(i)
  }
} else {
  for (let i = 0; i < props.digitCount; i++) {
    digits[i] = null
  }
}

const otpCont = ref(null)

const isDigitsFull = function () {
  for (const elem of digits) {
    if (elem === null || elem === undefined || elem === '') {
      return false
    }
  }
  return true
}

const handleKeyDown = function (event, index) {
  if (event.key !== 'Tab' && 
      event.key !== 'ArrowRight' &&
      event.key !== 'ArrowLeft'
  ) {
    event.preventDefault()
  }

  if (event.key === 'Backspace') {
    digits[index] = null
    if (index !== 0) {
      (otpCont.value.children)[index - 1].focus()
    } 
    return
  }

  if ((new RegExp('^([0-9])$')).test(event.key)) {
    digits[index] = event.key
    if (index !== props.digitCount - 1) {
      (otpCont.value.children)[index + 1].focus()
    }
  }
  
  if (isDigitsFull()) {
    emit('update:otp', digits.join(''))
  }
}

const handlePaste = function(event) {
  event.preventDefault();
  const pastedData = event.clipboardData.getData('text/plain').replace(/\D/g, '').slice(0, props.digitCount);
  for (let i = 0; i < pastedData.length; i++) {
    digits[i] = pastedData[i];
  }
  if (pastedData.length > 0) {
    const focusIndex = pastedData.length < props.digitCount ? pastedData.length : props.digitCount - 1;
    (otpCont.value.children)[focusIndex].focus();
  }
  if (isDigitsFull()) {
    emit('update:otp', digits.join(''))
  }
}
</script>

<style scoped>
.animate-bounce-short {
  animation: bounce-short 0.3s ease-in-out 1;
}

@keyframes bounce-short {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
</style>
