import {Construct, Stack, StackProps} from "@aws-cdk/core"
import {AssetCode, Code, LayerVersion} from "@aws-cdk/aws-lambda"
import * as fs from "fs"
import * as child_process from "child_process"
import * as path from "path"
import * as crypto from "crypto"

export class PythonStack extends Stack {
    private readonly projectDir: string
    public lambdaLayers: LayerVersion[]


    constructor(scope: Construct, constructId: string, props?: StackProps) {
        super(scope, constructId, props)

        this.projectDir = path.join('.', '..')
        this.lambdaLayers = [this.createDependenciesLayer()]
    }

    createDependenciesLayer(): LayerVersion {
        const layersDir = path.join(this.projectDir, '.layers')

        if (!fs.existsSync(layersDir)) {
            fs.mkdirSync(layersDir)
        }

        const stdout = child_process.execSync('../pw poetry export --with-credentials --without-hashes', {encoding: 'utf8'})
        let requirementsArray = stdout.match(/[^\r\n]+/g) || []
        requirementsArray = requirementsArray.filter(line => !line.startsWith('boto'))
        const requirements = requirementsArray.join('\n')
        const requirementsHash = crypto.createHash('md5').update(requirements).digest('hex')
        const destinationDir = path.join(layersDir, requirementsHash)
        const requirementsFile = path.join(destinationDir, 'requirements.txt')
        const pythonDir = path.join(destinationDir, 'python')

        if (!fs.existsSync(destinationDir)) {
            fs.mkdirSync(destinationDir)
        }
        if (!fs.existsSync(requirementsFile)) {
            fs.writeFileSync(requirementsFile, requirements)
        }
        if (!fs.existsSync(pythonDir)) {
            console.info('running pip install...')
            const result = child_process.spawnSync('pip3',
                ['install', '--no-deps', '-r', requirementsFile.toString(), '-t', pythonDir.toString()])
            if (result.status) {
                throw new Error(`pip3 install exited with non-zero code: ${result.status}`)
            }
        }
        const layerId = `${this.stackName}-dependencies`
        const layerCode = Code.fromAsset(destinationDir)
        return new LayerVersion(this, layerId, {code: layerCode})
    }

    createCodeAsset(relativePath: string): AssetCode {
        return Code.fromAsset(path.join(this.projectDir, relativePath))
    }
}
