// crates/capture/src/lib.rs
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use image::{DynamicImage, ImageFormat, GenericImageView, ImageEncoder};
use xcap::Monitor;
use std::io::Cursor;
use std::time::Duration;

// Configuration for the capture engine
#[derive(Debug, Clone)]
pub struct Config {
    pub interval: Duration,
    pub format: ImageFormat,
}

// Default configuration
impl Default for Config {
    fn default() -> Self {
        Self {
            interval: Duration::from_millis(1500),
            format: ImageFormat::Png,
        }
    }
}

// Representation of a captured frame
#[derive(Debug, Clone)]
pub struct Frame {
    pub id: i64,
    pub timestamp: DateTime<Utc>,
    pub data: Vec<u8>,
    pub width: u32,
    pub height: u32,
    pub format: String,
    pub size_bytes: i64,
}

// Capture engine
pub struct Engine {
    config: Config,
}

// Implementation of the capture engine
impl Engine {
    pub fn new(config: Config) -> Self {
        Self { config }
    }

    // Capture a frame
    pub fn capture_frame(&self, frame_id: i64) -> Result<Frame> {
        let image = self.capture_screen()?;
        let (width, height) = image.dimensions();
        
        let data = self.encode_image(&image)?;
        let size_bytes = data.len() as i64;

        Ok(Frame {
            id: frame_id,
            timestamp: Utc::now(),
            data,
            width,
            height,
            format: format!("{:?}", self.config.format).to_lowercase(),
            size_bytes,
        })
    }

    // Capture the screen and return as DynamicImage
    fn capture_screen(&self) -> Result<DynamicImage> {
        let monitors = Monitor::all()
            .context("Failed to enumerate monitors")?;
        
        let monitor = monitors
            .first()
            .context("No screens available")?;
        
        let screenshot = monitor
            .capture_image()
            .map_err(|e| anyhow::anyhow!(e))
            .context("Failed to capture screen")?;
        
        let image = DynamicImage::ImageRgba8(screenshot);
        
        Ok(image)
    }

    // Encode the image to the specified format
    fn encode_image(&self, img: &DynamicImage) -> Result<Vec<u8>> {
        let mut buffer = Cursor::new(Vec::new());
        
        match self.config.format {
            ImageFormat::Png => {
                img.write_to(&mut buffer, ImageFormat::Png)
                    .context("Failed to encode PNG")?;
            }
            ImageFormat::Jpeg => {
                img.write_to(&mut buffer, ImageFormat::Jpeg)
                    .context("Failed to encode JPEG")?;
            }
            _ => {
                img.write_to(&mut buffer, self.config.format)
                    .context("Failed to encode image")?;
            }
        }
        
        Ok(buffer.into_inner())
    }
}

// Function to compress PNG images
pub fn compress_png(img: &DynamicImage) -> Result<Vec<u8>> {
    let mut buffer = Cursor::new(Vec::new());
    
    // Use best compression for PNG
    let encoder = image::codecs::png::PngEncoder::new_with_quality(
        &mut buffer,
        image::codecs::png::CompressionType::Best,
        image::codecs::png::FilterType::Adaptive,
    );
    
    encoder.write_image(
        img.as_bytes(),
        img.width(),
        img.height(),
        img.color().into(),
    ).context("Failed to compress PNG")?;
    
    Ok(buffer.into_inner())
}

// Unit tests for the capture engine
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_engine_creation() {
        let config = Config::default();
        let engine = Engine::new(config);
        assert!(std::mem::size_of_val(&engine) > 0);
    }
}