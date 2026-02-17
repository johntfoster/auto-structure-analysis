/**
 * Tests for i18n multi-language support.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '../i18n/locales/en.json';
import es from '../i18n/locales/es.json';
import LanguageSwitcher from '../components/LanguageSwitcher';
import userEvent from '@testing-library/user-event';

// Create a test i18n instance
const testI18n = i18n.createInstance();
testI18n
  .use(initReactI18next)
  .init({
    lng: 'en',
    fallbackLng: 'en',
    resources: {
      en: { translation: en },
      es: { translation: es },
    },
    interpolation: {
      escapeValue: false,
    },
  });

describe('i18n Multi-language Support', () => {
  it('should have English translations', () => {
    expect(en.app.title).toBe('Auto Structure Analysis');
    expect(en.nav.home).toBe('Home');
    expect(en.editor.title).toBe('Model Editor');
  });

  it('should have Spanish translations', () => {
    expect(es.app.title).toBe('Análisis Automático de Estructuras');
    expect(es.nav.home).toBe('Inicio');
    expect(es.editor.title).toBe('Editor de Modelo');
  });

  it('should have matching keys in both languages', () => {
    const enKeys = getKeys(en);
    const esKeys = getKeys(es);
    
    expect(enKeys.sort()).toEqual(esKeys.sort());
  });

  it('should render language switcher', () => {
    render(
      <I18nextProvider i18n={testI18n}>
        <LanguageSwitcher />
      </I18nextProvider>
    );
    
    expect(screen.getByText(/Select Language/i)).toBeInTheDocument();
  });

  it('should switch between languages', async () => {
    const user = userEvent.setup();
    
    render(
      <I18nextProvider i18n={testI18n}>
        <LanguageSwitcher />
      </I18nextProvider>
    );
    
    const select = screen.getByRole('combobox');
    
    // Initial language is English
    expect(select).toHaveValue('en');
    
    // Switch to Spanish
    await user.selectOptions(select, 'es');
    expect(testI18n.language).toBe('es');
  });

  it('should have all required sections in translations', () => {
    const requiredSections = [
      'app',
      'nav',
      'home',
      'camera',
      'editor',
      'results',
      'loads',
      'materials',
      'units',
      'actions',
      'messages',
      'code'
    ];
    
    for (const section of requiredSections) {
      expect(en).toHaveProperty(section);
      expect(es).toHaveProperty(section);
    }
  });

  it('should have material translations', () => {
    expect(en.materials.steel).toBe('Steel A36');
    expect(es.materials.steel).toBe('Acero A36');
    
    expect(en.materials.aluminum).toBe('Aluminum 6061-T6');
    expect(es.materials.aluminum).toBe('Aluminio 6061-T6');
  });

  it('should have load case translations', () => {
    expect(en.loads.dead).toBe('Dead Load');
    expect(es.loads.dead).toBe('Carga Muerta');
    
    expect(en.loads.live).toBe('Live Load');
    expect(es.loads.live).toBe('Carga Viva');
    
    expect(en.loads.wind).toBe('Wind Load');
    expect(es.loads.wind).toBe('Carga de Viento');
  });

  it('should have code check translations', () => {
    expect(en.code.slenderness).toBe('Slenderness Ratio');
    expect(es.code.slenderness).toBe('Relación de Esbeltez');
    
    expect(en.code.compression).toBe('Compression Capacity');
    expect(es.code.compression).toBe('Capacidad a Compresión');
  });

  it('should have structure type translations', () => {
    expect(en.editor.truss).toBe('Truss');
    expect(es.editor.truss).toBe('Cercha');
    
    expect(en.editor.frame).toBe('Frame');
    expect(es.editor.frame).toBe('Marco');
  });
});

/**
 * Helper function to get all keys from an object recursively.
 */
function getKeys(obj: any, prefix = ''): string[] {
  return Object.keys(obj).reduce((keys: string[], key) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      return [...keys, ...getKeys(obj[key], path)];
    }
    return [...keys, path];
  }, []);
}
