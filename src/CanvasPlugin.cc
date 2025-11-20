#include <gazebo/rendering/rendering.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/common/Events.hh>
#include <gazebo/common/Time.hh>

#include <ignition/common/Image.hh>

#include <OgreTextureManager.h>
#include <OgreMaterialManager.h>
#include <OgreHardwarePixelBuffer.h>

#include <filesystem>
#include <vector>
#include <string>
#include <algorithm>
#include <cstring>
#include <functional>

namespace fs = std::filesystem;
namespace img_common = ignition::common;

using namespace gazebo;

class CanvasPlugin : public VisualPlugin
{
public:
  void Load(rendering::VisualPtr _visual, sdf::ElementPtr _sdf) override
  {
    this->visual = _visual;
    this->scene  = _visual->GetScene();

    // --- параметри з SDF ---
    this->width  = _sdf->HasElement("width")  ? _sdf->Get<int>("width")  : 1024;
    this->height = _sdf->HasElement("height") ? _sdf->Get<int>("height") : 1024;
    this->intervalSec = _sdf->HasElement("interval")
                        ? _sdf->Get<double>("interval")
                        : 5.0;

    if (_sdf->HasElement("images_dir"))
      this->imagesDir = _sdf->Get<std::string>("images_dir");

    gzmsg << "[CanvasPlugin] Load, size = " << this->width << "x" << this->height
          << ", images_dir = '" << this->imagesDir
          << "', interval = " << this->intervalSec << " s" << std::endl;

    // --- 1. Динамічна текстура ---
    this->texture = Ogre::TextureManager::getSingleton().createManual(
        "DynamicCanvasTexture",
        Ogre::ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME,
        Ogre::TEX_TYPE_2D,
        this->width, this->height,
        0,
        Ogre::PF_BYTE_BGRA,
        Ogre::TU_DYNAMIC_WRITE_ONLY_DISCARDABLE);

    if (this->texture.isNull())
    {
      gzerr << "[CanvasPlugin] Failed to create texture" << std::endl;
      return;
    }

    // --- 2. Свій матеріал + вішати на visual ---
    Ogre::String matName = "CanvasMaterial";
    Ogre::MaterialPtr mat =
        Ogre::MaterialManager::getSingleton().create(
            matName,
            Ogre::ResourceGroupManager::DEFAULT_RESOURCE_GROUP_NAME);

    Ogre::Technique *tech = mat->getTechnique(0);
    if (!tech)
      tech = mat->createTechnique();

    Ogre::Pass *pass = tech->getPass(0);
    if (!pass)
      pass = tech->createPass();

    pass->setLightingEnabled(false);

    Ogre::TextureUnitState *tu = pass->createTextureUnitState();
    tu->setTexture(this->texture);
    tu->setTextureAddressingMode(Ogre::TextureUnitState::TAM_CLAMP);

    this->visual->SetMaterial(matName);

    // --- 3. Збираємо картинки у директорії ---
    if (!this->imagesDir.empty())
      this->ScanImagesDir(this->imagesDir);

    if (this->imageFiles.empty())
    {
      gzerr << "[CanvasPlugin] No images found, filling solid blue" << std::endl;
      this->FillSolidColor(255, 0, 0, 255);
      return;
    }

    this->currentIndex = 0;
    if (!this->LoadImageToTexture(this->imageFiles[this->currentIndex]))
    {
      gzerr << "[CanvasPlugin] Failed to load first image, filling solid blue"
            << std::endl;
      this->FillSolidColor(255, 0, 0, 255);
    }
    else
    {
      gzmsg << "[CanvasPlugin] Shown image[0] = "
            << this->imageFiles[0] << std::endl;
    }

    // стартовий час по wall-time
    this->lastSwitchWall = common::Time::GetWallTime().Double();

    // --- 4. Підписка на PreRender (візуальний апдейт) ---
    this->updateConnection = event::Events::ConnectPreRender(
        std::bind(&CanvasPlugin::OnUpdate, this));
  }

private:
  // пошук картинок
  void ScanImagesDir(const std::string &_dir)
  {
    fs::path dir(_dir);
    if (!fs::exists(dir) || !fs::is_directory(dir))
    {
      gzerr << "[CanvasPlugin] images_dir is not a directory: "
            << _dir << std::endl;
      return;
    }

    std::vector<std::string> exts =
        {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"};

    for (const auto &entry : fs::directory_iterator(dir))
    {
      if (!entry.is_regular_file())
        continue;

      std::string ext = entry.path().extension().string();
      std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);

      if (std::find(exts.begin(), exts.end(), ext) != exts.end())
        this->imageFiles.push_back(entry.path().string());
    }

    std::sort(this->imageFiles.begin(), this->imageFiles.end());

    gzmsg << "[CanvasPlugin] Found " << this->imageFiles.size()
          << " images in " << _dir << std::endl;
  }

  // суцільний колір BGRA
  void FillSolidColor(uint8_t b, uint8_t g, uint8_t r, uint8_t a)
  {
    if (this->texture.isNull())
      return;

    Ogre::HardwarePixelBufferSharedPtr pb = this->texture->getBuffer();
    pb->lock(Ogre::HardwareBuffer::HBL_DISCARD);
    const Ogre::PixelBox &box = pb->getCurrentLock();

    uint8_t *dst = static_cast<uint8_t *>(box.data);
    const size_t pixels =
        static_cast<size_t>(this->width) *
        static_cast<size_t>(this->height);

    for (size_t i = 0; i < pixels; ++i)
    {
      dst[0] = b;
      dst[1] = g;
      dst[2] = r;
      dst[3] = a;
      dst += 4;
    }

    pb->unlock();
  }

  // завантаження PNG/JPG → RGB → BGRA → текстура
  bool LoadImageToTexture(const std::string &_filename)
  {
    img_common::Image img;
    if (img.Load(_filename) != 0 || !img.Valid())
    {
      gzerr << "[CanvasPlugin] Cannot load image: " << _filename << std::endl;
      return false;
    }

    if (static_cast<int>(img.Width()) != this->width ||
        static_cast<int>(img.Height()) != this->height)
    {
      gzmsg << "[CanvasPlugin] Rescaling image " << _filename << " from "
            << img.Width() << "x" << img.Height()
            << " to " << this->width << "x" << this->height << std::endl;
      img.Rescale(this->width, this->height);
    }

    unsigned char *rgbPtr = nullptr;
    unsigned int rgbSize  = 0;
    img.RGBData(&rgbPtr, rgbSize);

    if (rgbPtr == nullptr || rgbSize == 0)
    {
      gzerr << "[CanvasPlugin] RGBData empty for " << _filename << std::endl;
      return false;
    }

    const size_t pixels =
        static_cast<size_t>(this->width) *
        static_cast<size_t>(this->height);

    if (rgbSize < pixels * 3)
    {
      gzerr << "[CanvasPlugin] RGBData size mismatch for "
            << _filename << " (got " << rgbSize
            << ", expected at least " << pixels * 3 << ")" << std::endl;
      return false;
    }

    std::vector<unsigned char> bgra(pixels * 4);
    for (size_t i = 0; i < pixels; ++i)
    {
      size_t i3 = i * 3;
      size_t i4 = i * 4;

      unsigned char r = rgbPtr[i3 + 0];
      unsigned char g = rgbPtr[i3 + 1];
      unsigned char b = rgbPtr[i3 + 2];

      bgra[i4 + 0] = b;
      bgra[i4 + 1] = g;
      bgra[i4 + 2] = r;
      bgra[i4 + 3] = 255;
    }

    if (this->texture.isNull())
      return false;

    Ogre::HardwarePixelBufferSharedPtr pb = this->texture->getBuffer();
    pb->lock(Ogre::HardwareBuffer::HBL_DISCARD);
    const Ogre::PixelBox &box = pb->getCurrentLock();

    const size_t copySize =
        std::min(bgra.size(), static_cast<size_t>(box.getConsecutiveSize()));
    std::memcpy(box.data, bgra.data(), copySize);
    pb->unlock();

    gzmsg << "[CanvasPlugin] Loaded image to texture: " << _filename << std::endl;
    return true;
  }

  // тепер без параметрів, викликається з PreRender
  void OnUpdate()
  {
    if (this->imageFiles.empty())
      return;

    double now = common::Time::GetWallTime().Double();   // реальний час
    if (now - this->lastSwitchWall < this->intervalSec)
      return;

    this->lastSwitchWall = now;
    this->currentIndex = (this->currentIndex + 1) % this->imageFiles.size();
    const std::string &file = this->imageFiles[this->currentIndex];

    gzmsg << "[CanvasPlugin] Switching to image[" << this->currentIndex
          << "] = " << file << std::endl;

    if (!this->LoadImageToTexture(file))
    {
      gzerr << "[CanvasPlugin] Failed to load image in slideshow: "
            << file << std::endl;
    }
  }

private:
  rendering::VisualPtr visual;
  rendering::ScenePtr  scene;

  int         width{0};
  int         height{0};
  std::string imagesDir;

  std::vector<std::string> imageFiles;
  size_t      currentIndex{0};
  double      intervalSec{5.0};
  double      lastSwitchWall{0.0};

  Ogre::TexturePtr     texture;
  event::ConnectionPtr updateConnection;
};

GZ_REGISTER_VISUAL_PLUGIN(CanvasPlugin)
